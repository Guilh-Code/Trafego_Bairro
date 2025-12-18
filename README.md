<div align="center">

  <h1>🚦 Traffic Monitor & Analysis System</h1>
  
  <p>
    Um sistema de Visão Computacional e Engenharia de Dados para monitoramento de tráfego urbano, detecção de infrações e análise de fluxo em tempo real.
  </p>

  <p>
    <a href="#-sobre-o-projeto">Sobre</a> •
    <a href="#-arquitetura-e-tecnologias">Tecnologias</a> •
    <a href="#-funcionalidades-fase-1">Funcionalidades</a> •
    <a href="#-banco-de-dados">Dados</a> •
    <a href="#-roadmap">Roadmap</a>
  </p>

  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/YOLO-v8-green?style=for-the-badge&logo=opencv&logoColor=white">
  <img src="https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql&logoColor=white">
  <img src="https://img.shields.io/badge/STATUS-FASE%201%20(MVP)-orange?style=for-the-badge">

</div>

---

## 📖 Sobre o Projeto

Este projeto nasceu de uma necessidade real no meu bairro. Recentemente, a sinalização da minha rua foi alterada, tornando-a **mão única**. No entanto, muitos motoristas ainda não se adaptaram ou ignoram a sinalização, gerando riscos.

Como profissional de dados, decidi não apenas observar, mas **mensurar** esse problema. Desenvolvi um sistema que utiliza a câmera do meu celular (e futuramente uma câmera IP dedicada) para monitorar a rua, identificar veículos e, crucialmente, detectar quem está na contramão.

O objetivo não é apenas a detecção visual, mas a **Engenharia de Dados**: transformar pixels em linhas de banco de dados para futura análise de horários de pico, reincidência e tipos de veículos.

---

## 🛠 Arquitetura e Tecnologias

O sistema roda localmente utilizando o poder de processamento da GPU (CUDA) para inferência em tempo real.

<div align="center">
  <table>
    <tr>
      <td align="center"><b>Componente</b></td>
      <td align="center"><b>Tecnologia</b></td>
      <td align="center"><b>Função</b></td>
    </tr>
    <tr>
      <td>🧠 <b>Modelo de IA</b></td>
      <td>YOLOv8 (Ultralytics)</td>
      <td>Detecção de objetos (Carro, Moto, Ônibus, Caminhão)</td>
    </tr>
    <tr>
      <td>👁 <b>Visão Comp.</b></td>
      <td>OpenCV + Supervision</td>
      <td>Processamento de vídeo, tracking e lógica de linhas virtuais</td>
    </tr>
    <tr>
      <td>📝 <b>OCR / LPR</b></td>
      <td>EasyOCR</td>
      <td>Leitura de placas (License Plate Recognition)</td>
    </tr>
    <tr>
      <td>💾 <b>Banco de Dados</b></td>
      <td>PostgreSQL</td>
      <td>Armazenamento estruturado de cada evento</td>
    </tr>
    <tr>
      <td>🔌 <b>Hardware</b></td>
      <td>iPhone (Cam) + PC (RTX 5060)</td>
      <td>Captura e Processamento</td>
    </tr>
  </table>
</div>

---

## 🚀 Funcionalidades (Fase 1)

Atualmente, o **MVP (Mínimo Produto Viável)** já está operacional com as seguintes capacidades:

- [x] **Detecção e Classificação:** Identifica em tempo real se o objeto é Carro, Moto, Ônibus ou Caminhão.
- [x] **Lógica de Direção (Vector Logic):** Identifica se o veículo está na "Mão Certa" (Descendo) ou "Contramão" (Subindo) baseado no cruzamento de linhas virtuais calibradas na rua.
- [x] **Extração de Atributos:**
    - **Cor Predominante:** Algoritmo que recorta o veículo e define sua cor média.
    - **Leitura de Placa (Experimental):** Utiliza Deep Learning para tentar extrair a placa do veículo para análises de recorrência.
- [x] **Persistência de Dados:** Conexão automática com PostgreSQL, salvando o registro no exato momento da infração/passagem.

<div align="center">
  <img src="SEU_GIF_OU_IMAGEM_AQUI.gif" alt="Demo do Sistema" width="800">
  <p><em>Demonstração do sistema detectando veículos e direção em tempo real.</em></p>
</div>

---

## 💾 Banco de Dados

O foco deste projeto é gerar dados estruturados para análise. A tabela principal `registros_trafego` foi modelada da seguinte forma:

```sql
CREATE TABLE registros_trafego (
    id SERIAL PRIMARY KEY,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    placa_detectada VARCHAR(20),
    tipo_veiculo VARCHAR(20), -- Ex: 'carro', 'moto'
    cor_predominante VARCHAR(20),
    is_contramao BOOLEAN -- TRUE = Infração
);
```

---

## 🚧 Roadmap (Próximos Passos)

Este projeto está em evolução constante. Após a validação deste MVP, os próximos passos são:

- [ ] **Hardware Dedicado:** Instalação de uma câmera IP fixa para coleta de dados 24/7 (Experimento de 1 semana).
- [ ] **Dashboards (BI):** Conectar o Power BI ao PostgreSQL para visualizar:
    - Horários de maior infração.
    - Fluxo total de veículos por dia da semana.
    - Proporção de Carros x Motos.
- [ ] **Estimativa de Velocidade:** Implementar lógica de "Radar Virtual" medindo tempo entre dois pontos conhecidos (recurso testado, mas desativado temporariamente para calibração).
- [ ] **Deploy em Container:** Dockerizar a aplicação para fácil replicação.

---

## ⚖️ Nota Ética e Privacidade

A funcionalidade de **Leitura de Placas (OCR)** implementada neste projeto tem fins estritamente **acadêmicos e analíticos** (ex: entender a taxa de retorno de veículos na mesma rua ou diferenciar moradores de tráfego de passagem). Nenhuma imagem é armazenada permanentemente e nenhum dado é utilizado para denúncia ou fins legais. O foco é puramente Engenharia de Dados e Estudo de Fluxo.
