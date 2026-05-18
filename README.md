# 🧬 Synthetic Mapping Generator for CGRA and QCA

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![NetworkX](https://img.shields.io/badge/NetworkX-Graph_Processing-green.svg)](https://networkx.org/)

A procedural framework developed in Python for the large-scale generation of synthetic circuit mappings. The focus of this tool is to create topologically valid datasets for **Coarse-Grained Reconfigurable Architectures (CGRA)** and **Quantum-dot Cellular Automata (QCA)**, targeting the training of Artificial Intelligence models (such as Graph Neural Networks) applied to the Placement and Routing problem (Electronic Design Automation - EDA).

---

### ✨ Main Features (Generation Strategies)

The tool provides 4 distinct generation engines, tailored for different scenarios and technologies:

1. **CGRA - Systematic Grammar:** Procedural generation based on the topology of the physical interconnection network, applying formal rules (expansion, convergence, reconvergence) to achieve a fixed level of structural complexity.
2. **CGRA - Adaptive Grammar (Random):** Dynamically samples difficulty levels, adapting probability weights according to the generation success rate in order to maximize topological diversity.
3. **CGRA - Random Brute Force:** Ignores the restrictive grammar and generates purely random connections (controlled by an $\alpha$ factor), ideal for creating comparative *baselines* and testing the limits of the validation processor.
4. **QCA - Backwards Generation:** Dedicated strategy for QCA. Solves the *USE* and *2DDWave* clocking schemes while mitigating central congestion by routing wires from physical outputs to inputs, using a quadrant-density-based cost function.
5. **Integrated Validation:** Rigorous and automated verification of directed acyclic graphs (DAGs), connectivity, topological balance, and compliance with clocking rules.
6. **Visualization:** Automated generation of ASCII matrices in the terminal and high-resolution PNG images of the physical layout using Graphviz (Neato).

---

## 🛠️ Technologies Used

* **Language:** Python (3.8+)
* **Graph Processing:** `NetworkX` (Structural manipulation and validation).
* **Visualization:** `Graphviz` (Physical rendering engine).
* **CLI:** `argparse` for a modular and intuitive command-line interface.

---

## ⚙️ Installation and Setup

**1. Clone the repository:**
```bash
git clone https://github.com/El3ci0Sz/SMG-CGRA-QCA.git
cd SMG-CGRA-QCA
```

**2. Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

**3. Install the dependencies:**
```bash
pip install -r requirements.txt
```

🚀 **How to Use (CLI)**

The framework is fully operated through the command line. Below are usage examples for the 4 generation strategies.

**Generating Datasets for CGRA**

**1: Systematic Grammar.**

```bash
python scripts/runner.py --tec cgra --gen-mode grammar --strategy systematic --difficulty 5 --k-graphs 100 --arch-size 5 5 --output-dir datasets/cgra_grammar_systematic
```

**2: Adaptive Grammar.**

```bash
python scripts/runner.py --tec cgra --gen-mode grammar --strategy random --difficulty-range 1 10 --k-graphs 100 --arch-size 5 5 --output-dir datasets/cgra_grammar_random
```

**3: Random Brute Force.**

```bash
python scripts/runner.py --tec cgra --gen-mode random --alpha 0.35 --k-graphs 100 --arch-size 8 8 --output-dir datasets/cgra_random
```

**Generating Datasets for QCA**

**4: QCA Backwards (Reverse Generator).**

```bash
python scripts/runner.py --tec qca --qca-arch T --backwards --num-gates 20 --k-graphs 10 --arch-size 15 15 --visualize --output-dir datasets/qca_reverso
```
