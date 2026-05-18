# 🧬 Synthetic Mapping Generator for CGRA and QCA

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![NetworkX](https://img.shields.io/badge/NetworkX-Graph_Processing-green.svg)](https://networkx.org/)

A procedural framework developed in Python for the large-scale generation of synthetic circuit mappings. The focus of this tool is to create topologically valid datasets for **Coarse-Grained Reconfigurable Architectures (CGRA)** and **Quantum-dot Cellular Automata (QCA)**, targeting the training of Artificial Intelligence models (such as Graph Neural Networks) applied to the Placement and Routing problem (Electronic Design Automation - EDA).

---

### ✨ Main Features (Generation Strategies)

The tool provides 4 distinct generation engines, tailored for different scenarios and technologies:

1. **CGRA - Systematic Grammar:** Procedural generation based on the topology of the physical interconnection network, applying formal rules (tree, convergence, reconvergence) to achieve a fixed level of structural complexity.
2. **CGRA - Adaptive Grammar (Random):** Dynamically samples difficulty levels, adapting probability weights according to the generation success rate in order to maximize topological diversity.
3. **CGRA - Random Brute Force:** Ignores the restrictive grammar and generates purely random connections (controlled by an $\alpha$ factor).
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

## 📋 Command Line Interface (CLI) Arguments

The framework behavior is highly customizable through CLI arguments. The following table details the primary parameters used for generating benchmarks and datasets.

### 🏛️ Architecture Configurations

| Argument | Description | Example / Valid Values |
| :--- | :--- | :--- |
| `--arch-size` | Defines the dimensions of the CGRA grid (Rows x Columns). | `4 4`, `8 8` |
| `--bits` | 4-bit string that defines the interconnection topology. | `1000` (Mesh), `1001` (Mesh + Toroidal), `1010` (Mesh + One-Hop), `1111` (All) |
| `--ii` | Defines a fixed Initiation Interval. If omitted, the II is calculated dynamically based on the used resources. | `1`, `2`, `3` |
| `--qca-arch` | QCA clocking architecture type. | `U`, `R`, `T` |

### 🧩 Graph Generation Configurations

| Argument | Description | Example / Valid Values |
| :--- | :--- | :--- |
| `--gen-mode` | Operation mode for the generator. | `grammar` (procedural generation), `random` |
| `--graph-range` | Target size range (minimum and maximum number of nodes) for the generated DFGs. | `3 70`, `3 16` |
| `--difficulty` | The complexity level of the grammatical recipe. It can also accept a special flag to switch from systematic to smart random strategy. | `1` to `20` |
| `--k-graphs` | The number of graphs to be generated per task. | `100`, `10000` |
| `--strategy` | Defines the difficulty mapping strategy. | `systematic`, `random` |
| `--difficulty-range` | Defines the range of recipes used when the strategy is set to random. | `1 10` |
| `--alpha` | Probability factor used to generate random edges in the brute-force method. | `0.35` |
| `--num-gates` | Number of logic gates to target in the Backwards QCA generation. | `20` |
| `--backwards` | Flag to enable the Backwards generation logic specific to QCA. | (Flag) |

### ⚙️ Execution Configurations

| Argument | Description | Example / Valid Values |
| :--- | :--- | :--- |
| `--output-dir` | Root directory where the output results (`.dot`, `.json`, `.png`) will be saved. | `datasets/cgra_grammar` |
| `--no-images` | Disables the generation of PNG images of the graphs to save disk space and CPU time. | (Flag) |
| `--visualize` | Enables the generation of visual grids and layout outputs for the generated architectures. | (Flag) |
| `--workers` | Number of parallel processes. If not defined, it uses all available cores. | `4`, `8` |

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
