# 🤖 Automação de CNC para Fenotipagem em Agricultura de Ambiente Controlado  
### TCC - Universidade Federal de Viçosa (UFV)  
Bem-vindo ao projeto de automação de uma máquina CNC (Comando Numérico Computadorizado) para integrar a fenotipagem de alto rendimento no Laboratório de Agricultura em Ambiente Controlado da UFV (LAAC)!  

---

## 📝 Sobre o Projeto  
Este trabalho de conclusão de curso desenvolve um sistema de automação para uma **máquina CNC** localizada em uma **câmara de simulação de ambientes**. O objetivo é programar a CNC para percorrer uma mesa de fenotipagem, seguindo um caminho planta a planta, capturando imagens detalhadas para análise fenotípica.  

💡 **Finalidade:**  
- Automatizar a captura de imagens de plantas em um ambiente controlado;  
- Facilitar a operação do equipamento com inserção de programações operacionais;  
- Contribuir para estudos de fenotipagem de alto rendimento.  

---

## 🌟 Funcionalidades  
- **Caminhamento Planta a Planta:** A CNC segue uma trajetória mais curta possível, visitando cada planta na mesa de fenotipagem;  
- **Captura de Imagens:** Integração com uma câmera RGB e uma Multispectral para registrar imagens de alta qualidade;  
- **Ambiente Controlado:** Operação dentro de uma câmara que simula condições ambientais específicas (luz, temperatura, umidade etc.);  
- **Fenotipagem Automatizada:** As imagens capturadas são usadas para análise de características das plantas (crescimento, saúde, etc.).  

---

## 🛠️ Tecnologias Utilizadas  
| Tecnologia       | Função                          |  
|-------------------|---------------------------------|  
| **CNC**          | Movimento preciso na mesa       |  
| **Arduino Mega** | Controle e programação |  
| **Câmera**       | Captura de imagens das plantas  |  
| **Python**       | Scripts de automação  |  

---

## ⚙️ Como Funciona  
1. **Configuração da Mesa:** As plantas são dispostas em uma grade na mesa de fenotipagem;  
2. **Programação do Caminho:** A CNC é programada para seguir coordenadas específicas (ex.: X, Y);  
3. **Captura de Dados:** A câmera acoplada à CNC registra imagens em cada vaso ao longo da trajetória.    

![Mesa de Fenotipagem](https://github.com/A-malta/TCC/blob/beta/images/PhenotypingRoom.jpg)   

---

## 📦 Instalação e Uso  
### Pré-requisitos  
- Máquina CNC configurada.  
- Software de controle (GRBL).  
- Câmera compatível com o sistema.  

### Passos  
1. Clone este repositório:  
   ```powershell
   git clone https://github.com/A-malta/TCC.git
   ```
2. Configure as coordenadas da CNC e outros detalhes no arquivo `config.json`.  
3. Execute o script principal:  
   ```powershell
   python main.py
   ```

---

## 📷 Resultados Esperados  
- **Imagens de Alta Qualidade:** Registro visual detalhado de cada planta;  
- **Eficiência:** Redução do tempo de fenotipagem manual;  
- **Dados Precisos:** Informações quantitativas e qualitativas para pesquisa agrícola;  

![Exemplo de Imagem Capturada](link-para-imagem/imagem_planta.jpg)  
*(Adicione imagem aqui)*  

---

## 🤝 Contribuições  
Este é um projeto acadêmico ainda fechado. No futuro, sugestões serão bem-vindas!  
- Abra uma *issue* para reportar problemas ou ideias.  
- Faça um *fork* e envie um *pull request* com melhorias.  

---

## 🔗 Referências  
- [Wiki GRBL](https://github.com/gnea/grbl/wiki)
- [Lista dos comandos G-code mais importantes](https://howtomechatronics-com.translate.goog/tutorials/g-code-explained-list-of-most-important-g-code-commands/?_x_tr_sl=en&_x_tr_tl=pt&_x_tr_hl=pt&_x_tr_pto=tc)
- [Linkedin LAAC](https://www.linkedin.com/company/laac-ufv/posts/?feedView=all)
- [Instagram LAAC](https://www.instagram.com/laac.ufv/)
- [Instagram Spectral Int](https://www.instagram.com/spectral_int/)

---

## 💪 Equipe  
- **Autor:** [Aline Malta - UFV]  
- **Orientador:** [André Coelho - UFV]
- **Coorientador** [Jardel Fialho - UFV]
- **Instituição:** Universidade Federal de Viçosa (UFV)  

---

🌱 **"A tecnologia a serviço da agricultura do presente!"** 🌱  
*Projeto desenvolvido em 2025 para o TCC na área de automação e agricultura de precisão.*

---
