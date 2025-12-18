import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import cv2
from ultralytics import YOLO
import supervision as sv
import numpy as np
import psycopg2
import easyocr # <--- O NOVO JOGADOR

# --- CONFIGURAÇÃO ---
VIDEO_SOURCE = "teste_video.MOV" # Teste nos vídeos gravados primeiro!
# VIDEO_SOURCE = 0 

MODEL_NAME = "yolov8m.pt"

# Conexão BD
DB_PARAMS = {
    "dbname": "trafego_bairro",
    "user": "postgres",
    "password": "postgres123",
    "host": "localhost",
    "port": "5432"
}

CLASS_MAPPING = { 2: 'carro', 3: 'moto', 5: 'onibus', 7: 'caminhao' }

# INICIALIZA O LEITOR DE PLACAS (Usa a GPU RTX 5060)
print("🧠 Carregando modelo de leitura de placas (EasyOCR)...")
reader = easyocr.Reader(['en'], gpu=True) 

# --- FUNÇÃO DE COR ---
def detectar_cor_predominante(frame, bbox):
    x1, y1, x2, y2 = map(int, bbox)
    h, w, _ = frame.shape
    x1 = max(0, x1); y1 = max(0, y1); x2 = min(w, x2); y2 = min(h, y2)
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0: return "desconhecida"
    
    ch, cw, _ = crop.shape
    centro_crop = crop[int(ch*0.25):int(ch*0.75), int(cw*0.25):int(cw*0.75)]
    if centro_crop.size == 0: centro_crop = crop
    
    media_bgr = np.mean(centro_crop, axis=(0, 1))
    
    cores_conhecidas = {
        "preto": (40, 40, 40),
        "branco": (230, 230, 230),
        "prata": (192, 192, 192),
        "cinza": (128, 128, 128),
        "vermelho": (0, 0, 200),
        "azul": (200, 0, 0),
        "amarelo": (0, 255, 255)
    }
    
    menor_distancia = float('inf')
    nome_cor = "indefinida"
    for nome, valor_bgr in cores_conhecidas.items():
        dist = np.linalg.norm(media_bgr - np.array(valor_bgr))
        if dist < menor_distancia:
            menor_distancia = dist
            nome_cor = nome
    return nome_cor

# --- NOVA FUNÇÃO: LER PLACA ---
def ler_placa_automovel(frame, bbox):
    x1, y1, x2, y2 = map(int, bbox)
    h_img, w_img, _ = frame.shape
    
    # Proteção de coordenadas
    x1 = max(0, x1); y1 = max(0, y1); x2 = min(w_img, x2); y2 = min(h_img, y2)
    
    # Recorta o carro
    carro_crop = frame[y1:y2, x1:x2]
    if carro_crop.size == 0: return "ILEGIVEL"

    # ESTRATÉGIA: A placa geralmente está na metade de baixo do carro
    # Vamos cortar só a metade inferior para o OCR não ler "Chevrolet" no vidro
    h_car, w_car, _ = carro_crop.shape
    metade_inferior = carro_crop[int(h_car * 0.5):, :] # Pega do meio pra baixo
    
    # Pré-processamento (Deixa Preto e Branco para facilitar a leitura)
    gray = cv2.cvtColor(metade_inferior, cv2.COLOR_BGR2GRAY)
    
    # Manda o EasyOCR ler
    # detail=0 retorna só o texto. allowlist ajuda a filtrar só letras e numeros
    try:
        resultado = reader.readtext(gray, detail=0, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    except:
        return "ERRO_OCR"
    
    # Filtra o melhor resultado (Placas tem geralmente entre 5 a 7 caracteres)
    placa_final = "ILEGIVEL"
    for texto in resultado:
        if len(texto) >= 5: # Ignora lixo pequeno tipo "BR" ou parafusos
            placa_final = texto
            break # Pega o primeiro que parecer uma placa
            
    return placa_final

def salvar_no_banco(tipo, cor, placa, is_contramao):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        query = """
            INSERT INTO registros_trafego 
            (tipo_veiculo, cor_predominante, placa_detectada, is_contramao)
            VALUES (%s, %s, %s, %s)
        """
        # Se a placa for ilegível, salvamos NULL ou o texto "ILEGIVEL"
        if placa == "ILEGIVEL": placa = None 
        
        cursor.execute(query, (tipo, cor, placa, is_contramao))
        conn.commit()
        cursor.close()
        conn.close()
        
        direcao = "🚨 CONTRA-MÃO" if is_contramao else "✅ MÃO CERTA"
        print(f"💾 SALVO: {tipo.upper()} | Cor: {cor} | Placa: {placa if placa else '---'} | {direcao}")
    except Exception as e:
        print(f"❌ ERRO AO SALVAR: {e}")

def main():
    print("🚀 SISTEMA COMPLETO: Detecção + Cor + Placa (LPR)...")
    
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print("❌ Erro ao abrir vídeo.")
        return

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"📷 Resolução: {width}x{height}")

    model = YOLO(MODEL_NAME)
    
    # --- LINHA VIRTUAL ---
    if width > 1000:
        START = sv.Point(50, 1000) 
        END = sv.Point(1800, 850)
    else:
        START = sv.Point(20, height - 20)
        END = sv.Point(width - 20, height // 2)
    
    line_zone = sv.LineZone(start=START, end=END)

    # Annotators
    box_annotator = sv.BoxAnnotator(thickness=2)
    label_annotator = sv.LabelAnnotator(text_thickness=2, text_scale=0.8)
    trace_annotator = sv.TraceAnnotator(thickness=2, trace_length=40) 
    line_zone_annotator = sv.LineZoneAnnotator(thickness=3, text_thickness=2, text_scale=0.8, color=sv.Color.RED)
    dot_annotator = sv.DotAnnotator(position=sv.Position.BOTTOM_CENTER, radius=8, color=sv.Color.YELLOW)

    byte_tracker = sv.ByteTrack()

    print("🔴 Processando... (Aguarde o download do EasyOCR na primeira vez)")

    while True:
        ret, frame = cap.read()
        if not ret: break

        results = model(frame)[0]
        detections = sv.Detections.from_ultralytics(results)
        detections = detections[np.isin(detections.class_id, [2, 3, 5, 7])]
        detections = byte_tracker.update_with_detections(detections)
        
        cross_in, cross_out = line_zone.trigger(detections=detections)
        
        # --- LÓGICA UNIFICADA ---
        # Função auxiliar para processar quem cruzou a linha
        def processar_cruzamento(indices_cruzamento, is_contramao):
            if indices_cruzamento.any():
                for i, cruzou in enumerate(indices_cruzamento):
                    if cruzou:
                        class_id = detections.class_id[i]
                        nome_veiculo = CLASS_MAPPING.get(class_id, 'veiculo')
                        bbox = detections.xyxy[i]
                        
                        # 1. Detectar Cor
                        cor = detectar_cor_predominante(frame, bbox)
                        
                        # 2. Ler Placa (AQUI É O PESO PESADO!)
                        # Só lê a placa se for carro/caminhão. Moto é muito difícil.
                        placa = "---"
                        if class_id in [2, 5, 7]: # Carro, Onibus, Caminhao
                            placa = ler_placa_automovel(frame, bbox)
                        
                        salvar_no_banco(nome_veiculo, cor, placa, is_contramao)

        # Verifica entradas e saídas
        processar_cruzamento(cross_in, False) # Mão Certa
        processar_cruzamento(cross_out, True) # Contra-mão

        # Desenho
        annotated_frame = frame.copy()
        annotated_frame = trace_annotator.annotate(scene=annotated_frame, detections=detections)
        annotated_frame = line_zone_annotator.annotate(annotated_frame, line_counter=line_zone)
        annotated_frame = dot_annotator.annotate(scene=annotated_frame, detections=detections)
        annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=detections)
        
        labels = [f"#{tracker_id} {CLASS_MAPPING.get(class_id,'v')}" for tracker_id, class_id in zip(detections.tracker_id, detections.class_id)]
        annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)

        frame_resized = cv2.resize(annotated_frame, (1280, 720))
        cv2.imshow("Monitoramento Completo - APE Technology", frame_resized)
        
        if cv2.waitKey(1) == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()