# 🧬 Synthetic Mapping Generator para CGRA e QCA

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![NetworkX](https://img.shields.io/badge/NetworkX-Graph_Processing-green.svg)](https://networkx.org/)

Um framework procedural de desenvolvido em Python para a geração em larga escala de mapeamentos sintéticos de circuitos. O foco desta ferramenta é criar datasets topologicamente válidos para **Arquiteturas Reconfiguráveis de Granularidade Grossa (CGRA)** e **Autômatos Celulares de Pontos Quânticos (QCA)**, visando o treinamento de modelos de Inteligência Artificial (como Graph Neural Networks) aplicados ao problema de Posicionamento e Roteamento (Electronic Design Automation - EDA).

---

### ✨ Principais Funcionalidades (Estratégias de Geração)

A ferramenta possui 4 motores distintos de geração, ajustados para diferentes cenários e tecnologias:

1. **CGRA - Gramática Sistemática:** Geração processual baseada na topologia da rede de interconexão física, aplicando regras formais (expansão, convergência, reconvergência) para atingir um nível de dificuldade estrutural fixo.
2. **CGRA - Gramática Adaptativa (Random):** Sorteia dinamicamente os níveis de dificuldade, adaptando os pesos de probabilidade com base na taxa de sucesso da geração para maximizar a diversidade topológica.
3. **CGRA - Força Bruta Aleatória:** Ignora a gramática restritiva e gera conexões puramente aleatórias (controladas por um fator $\alpha$), ideal para criar *baselines* comparativos e testar os limites do processador de validação.
4. **QCA - Geração Reversa (Backwards):** Estratégia dedicada para QCA. Resolve o esquema de clock *USE* e *2DDWave* mitigando o congestionamento central ao rotear os fios das saídas físicas para as entradas, utilizando uma função de custo baseada na densidade de quadrantes.
5. **Validação Integrada:** Checagem rigorosa e automatizada de grafos acíclicos direcionados (DAGs), conectividade, balanço topológico e conformidade com as regras de *clock*.
6. **Visualização:** Geração automatizada de matrizes ASCII no terminal e imagens PNG de alta resolução do layout físico utilizando Graphviz (Neato).

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python (3.8+)
* **Processamento de Grafos:** `NetworkX` (Manipulação e validação estrutural).
* **Visualização:** `Graphviz` (Motor de renderização física).
* **CLI:** `argparse` para uma interface de linha de comando modular e intuitiva.

---

## ⚙️ Instalação e Configuração

**1. Clone o repositório:**
```
git clone https://github.com/El3ci0Sz/SMG_CGRA-QCA.git
cd SMG_CGRA-QCA
```
**2. Crie um ambiente virtual:**
```
python3 -m venv venv
source venv/bin/activate  # No Windows use: venv\Scripts\activate
```

**3. Instale as dependências:**
```
pip install -r requirements.txt
```

🚀 **Como Utilizar (CLI)**

O framework é operado inteiramente via linha de comando . Abaixo estão os exemplos de uso para as 4 estratégias de geração.

**Gerando Datasets para CGRA** 

**1: Gramática Sistemática.** 

python scripts/runner.py --tec cgra --gen-mode grammar --strategy systematic --difficulty 5 --k-graphs 100 --arch-size 5 5 --output-dir datasets/cgra_grammar_systematic

**2: Gramática Adaptativa.** 

python scripts/runner.py --tec cgra --gen-mode grammar --strategy random --difficulty-range 1 10 --k-graphs 100 --arch-size 5 5 --output-dir datasets/cgra_grammar_random

**3: Força Bruta Aleatória.** 

python scripts/runner.py --tec cgra --gen-mode random --alpha 0.35 --k-graphs 100 --arch-size 8 8 --output-dir datasets/cgra_random

**Gerando Datasets para QCA** 

**4: QCA Backwards (Gerador Reverso).** 

python scripts/runner.py --tec qca --qca-arch T --backwards --num-gates 20 --k-graphs 10 --arch-size 15 15 --visualize --output-dir datasets/qca_reverso
