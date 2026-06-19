---
name: sciplot-skill
description: >-
  Scientific visualization architect that transforms raw tabular data (CSV or similar)
  into elegant, publication-ready Python plotting code meeting the strict standards of
  high-impact journals (Nature, Science, Cell, Nature Communications).

  USE THIS SKILL whenever the user asks to: create a figure or plot from a data file,
  generate publication-quality charts, visualize CSV/tabular data scientifically, make
  scatter plots / boxplots / multi-panel figures, add statistical annotations (p-values,
  regression lines, confidence intervals), produce journal-ready figures, or requests
  any chart that needs to look "clean", "publication-quality", or "like a Nature paper".
  Also trigger when the user says things like "make a nice plot", "generate visualization
  code", "plot X vs Y from my data", or "create a figure for my manuscript".
---

# SciPlot Architect

## Overview
The `sciplot-skill` is an instruction-only skill designed to guide the agent in generating copy-pasteable, publication-ready Python plotting scripts. It enforces Matplotlib's object-oriented API standards, specific typography (Arial/Helvetica), colorblind-safe color schemes (such as Okabe-Ito), and high-resolution output formats (PDF/SVG at 300+ DPI) matching top-tier scientific journal specifications (e.g., *Nature*, *Science*, *Cell*, *Nature Communications*).

## Dependencies
This is a reasoning-only skill and does not execute any command-line helper scripts directly. However, the generated Python scripts depend on the following Python packages:
- `pandas` and `numpy` (for data manipulation)
- `matplotlib` and `seaborn` (for plotting and styling)
- `scipy` (for scientific computations, regression, and fitting)
- `statannotations` (optional, for significance brackets)

If packages are missing, provide the exact pip install command — do not create or activate any conda/virtual environment.

## Quick Start
When asked to visualize data, start with the standard object-oriented template. Note the use of global color dictionaries, LaTeX scientific units formatting, and frame-free legends:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

# 1. Global Group-to-Color Mapping for cross-figure consistency
GROUP_COLORS = {
    "Control": "#009E73",      # Okabe-Ito green
    "Treatment A": "#E69F00",  # Okabe-Ito orange
    "Treatment B": "#56B4E9"   # Okabe-Ito sky blue
}

# 2. Typography & RC Parameters
_available = {f.name for f in fm.fontManager.ttflist}
_sans = next((f for f in ["Arial", "Helvetica", "DejaVu Sans"] if f in _available), "sans-serif")

plt.rcParams.update({
    "font.family":      "sans-serif",
    "font.sans-serif":  [_sans],
    "font.size":        8,
    "axes.titlesize":   9,
    "axes.labelsize":   10,
    "xtick.labelsize":  8,
    "ytick.labelsize":  8,
    "legend.fontsize":  8,
    "figure.dpi":       300,
})

# Example data
np.random.seed(42)
df = pd.DataFrame({
    "group": np.repeat(["Control", "Treatment A", "Treatment B"], 20),
    "response": np.concatenate([np.random.normal(10, 1.5, 20),
                                np.random.normal(12, 1.8, 20),
                                np.random.normal(15, 2.0, 20)])
})

# 3. Figure Layout (Single-column width: 3.5 inches)
fig, ax = plt.subplots(figsize=(3.5, 3.0))

# 4. Use box/violin/strip overlay instead of dynamite bar charts
sns.boxplot(
    data=df, x="group", y="response", ax=ax,
    palette=GROUP_COLORS, width=0.4, flierprops={"marker": "none"}
)
sns.stripplot(
    data=df, x="group", y="response", ax=ax,
    color="0.3", alpha=0.5, size=3, jitter=0.15
)

# 5. Scientific Units using LaTeX index notation and despine
ax.set_xlabel("Experimental Group")
ax.set_ylabel(r"Growth Rate ($\mathrm{mm\ d^{-1}}$)")  # index notation
sns.despine(ax=ax)

# 6. Save figure as vector PDF
fig.savefig("figure.pdf", dpi=300, bbox_inches="tight")
plt.close(fig)
```

## Workflow
Follow these numbered steps for plotting and code generation tasks:

### 1. Check Dependencies
Before writing any code, check whether the required libraries are importable in the user's environment. Instruct the user to run:

```python
import importlib
for pkg in ["pandas", "numpy", "matplotlib", "seaborn", "statannotations"]:
    status = "OK" if importlib.util.find_spec(pkg) else "MISSING"
    print(f"{pkg}: {status}")
```

If any library is **MISSING**, output the exact pip install command before continuing:
```bash
pip install <missing-package>
```
Never create or activate a conda/virtual environment — just pip.

### 2. Inspect Data Quality and Clarify
Read the CSV or data file directly, or ask the user to provide column names, data types, and the first few rows. Specifically identify:
- Column names and data types.
- The target/response variables.
- NaN values, missing records, or obvious outliers.
- The number of observations ($N$).

If you detect NaN values or potential outliers, pause and ask the user:
> "I found [X] NaN values in column [Y] and [describe outlier if any]. How would you like to handle them?
> (a) Drop rows silently
> (b) Fill with column median
> (c) Keep as-is and let matplotlib skip them
> (d) Other — tell me."

Do not proceed to code generation until the data is clean or the user has provided guidance.

### 3. Propose Plot Architecture
Propose a plot design in 1-2 sentences including the layout, plot type, and color scheme, explaining how it fits the scientific message. Obtain confirmation (implicit or explicit) before generating the full script.

*Example Proposal:*
> "I'll use a box plot + strip overlay (single-column, 89 mm) with a custom group-to-color dictionary mapping WT to green and KO to vermilion. The $N=20$ per group fits the low-N scatter rule."

### 4. Generate Code following Layout and Design Standards
Write the full Python script adhering to the following rules:

- **Ban "Dynamite Plots" (No Bar Charts for Distributions):** Never use bar charts with error bars to display continuous distributions. High-impact journals require showing the data structure. Use one of the following:
  - **Box Plots:** `sns.boxplot` with `flierprops={"marker": "none"}` to hide duplicate outlier representations if overlaying points.
  - **Violin Plots:** `sns.violinplot` with transparent or thin inner structures.
  - **Raincloud/Hybrid Plots:** Overlaying half-violins (using `ptitprince` or custom path collections), box plots, and individual jittered strip points (`sns.stripplot`).
- **Define a Global Group-to-Color Dictionary:** To ensure strict color consistency across multiple panels or separate figures, always define a mapping dictionary (e.g. `GROUP_COLORS = {"Control": "#009E73", "KO": "#D55E00"}`) and pass it to the plotting functions via the `palette` or `color` argument.
- **Scientific Unit Notation:** Always use standard scientific index notation (with negative exponents and math-mode formatting) for units in axis labels. Do not use slashes.
  - *Correct:* `r"Growth Rate ($\mathrm{mm\ d^{-1}}$)"`, `r"Velocity ($\mathrm{m\ s^{-1}}$)"`, `r"Concentration ($\mathrm{g\ L^{-1}}$)"`
  - *Incorrect:* `"Growth Rate (mm/day)"`, `"Velocity (m/s)"`
- **Clean Legend Aesthetics:** Always remove the legend bounding box using `frameon=False`. Position the legend strategically so that it does not overlap with data points or margins, using outer legends (`bbox_to_anchor`) when space is tight.
  ```python
  ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1))
  ```
- **Journal Layout Sizes:** Enforce exact sizes using `fig.set_size_inches(width_in, height_in)`:
  - Single Column: 89 mm (3.50 inches)
  - 1.5 Column: 136 mm (5.35 inches)
  - Double Column: 183 mm (7.20 inches)
- **Typography:** Apply the typography RC parameters from the Quick Start section. For multi-panel figures, label panels with **12 pt bold** letters at `(-0.15, 1.02)` in axes coordinates.
- **Color Palettes:**
  - Categorical data: Okabe-Ito palette (`["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#000000"]`).
  - Continuous data: `viridis`, `magma`, or `cividis`.
  - Diverging data: `RdBu_r` or `coolwarm`.
- **Axes & Spines:** Use `sns.despine(ax=ax)` to remove top and right spines. Set subtle grid lines with `ax.yaxis.grid(True, linewidth=0.4, color="0.85", zorder=0)` and call `ax.set_axisbelow(True)`.
- **Significance & Regression:**
  - Add error bars (SEM/SD) or box/whisker indicators for variance.
  - Use `statannotations` for pairwise comparisons when applicable.
  - Print $R^2$ and exact $p$-value for regressions:
    ```python
    slope, intercept, r, p, _ = stats.linregress(x, y)
    r2_label = f"$R^2={r**2:.2f}$\n$p={p:.3f}$" if p >= 0.001 else f"$R^2={r**2:.2f}$\n$p<0.001$"
    ax.text(0.05, 0.92, r2_label, transform=ax.transAxes, fontsize=8, va="top")
    ```
- **Low-N Overlay Rule:** If $N < 30$ per group, overlay individual points on top of box or violin plots using `sns.stripplot` with a small size and jitter.
- **Layouts:** Use `subplot_mosaic` for non-uniform panels and `GridSpec` for uniform grids.
- **Exporting Figures:** Save figures in PDF format at 300 DPI with `bbox_inches="tight"` and close the figure to avoid memory leaks.

### 5. Handle Errors on Failures
If the generated script raises an error:
1. Examine the traceback and identify the root cause.
2. Produce a corrected script and explain the changes.
3. If the error is caused by a missing optional package (like `statannotations`), provide an alternative version that works without it (e.g., using matplotlib/scipy manually).

### 6. Generate Reusable Stylesheets (Optional)
If requested, generate a `nature_standards.mplstyle` file allowing the user to load styles globally:
```ini
# nature_standards.mplstyle
font.family         : sans-serif
font.sans-serif     : Arial, Helvetica, DejaVu Sans
font.size           : 8
axes.labelsize      : 10
axes.titlesize      : 9
xtick.labelsize     : 8
ytick.labelsize     : 8
legend.fontsize     : 8
figure.dpi          : 300
axes.spines.top     : False
axes.spines.right   : False
axes.grid           : True
axes.axisbelow      : True
grid.color          : 0.85
grid.linewidth      : 0.4
savefig.bbox        : tight
savefig.format      : pdf
```

## Rate Limiting
Not applicable. This skill does not make external web/API calls directly.

## Common Mistakes
1. **Using Default Matplotlib Styles:** Relying on default fonts (sans-serif fallbacks not configured), standard colors (e.g., `tab10` instead of Okabe-Ito), or keeping top and right spines visible.
2. **Procedural Pyplot Commands:** Mixing the state-machine interface (`plt.plot`, `plt.title`) with the object-oriented API (`ax.plot`, `ax.set_title`). Keep code strictly object-oriented.
3. **Omitting Low-N Data Points or Using Dynamite Plots:** Using bar charts with error bars for continuous data, or failing to overlay raw scatter points on box/violin plots when $N < 30$, hiding true sample distribution.
4. **Poor Legend Aesthetics and Axis Notation:** Leaving standard borders on legends (`frameon=True`), or using slash-based unit representations like `m/s` or `g/L` instead of scientific index notations.
5. **Ignoring Constraints:** Generating 3D plots, pie charts, or using synthetic data without explicit user request.
