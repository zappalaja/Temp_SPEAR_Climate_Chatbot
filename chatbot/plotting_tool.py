"""
Plotting Tool for Climate Data Visualization
Allows the model to generate matplotlib plots that are displayed in Streamlit
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Any
import json


def create_plot(
    plot_type: str,
    data: Dict[str, Any],
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    style: Optional[Dict[str, Any]] = None
) -> plt.Figure:
    """
    Create a matplotlib plot based on specifications from the model.

    Args:
        plot_type: Type of plot ("line", "bar", "scatter", "heatmap", "contour")
        data: Dictionary containing plot data:
            - For line/bar/scatter: {"x": [...], "y": [...], "labels": [...] (optional)}
            - For heatmap/contour: {"z": [[...]], "x": [...] (optional), "y": [...] (optional)}
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        style: Optional styling parameters (colors, markers, etc.)

    Returns:
        matplotlib Figure object
    """
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Set default style if not provided
    if style is None:
        style = {}

    # Get data arrays
    if plot_type in ["line", "bar", "scatter"]:
        x = data.get("x", [])
        y = data.get("y", [])
        labels = data.get("labels", None)

        if plot_type == "line":
            color = style.get("color", "steelblue")
            linewidth = style.get("linewidth", 2)
            marker = style.get("marker", "o")
            ax.plot(x, y, color=color, linewidth=linewidth, marker=marker,
                   markersize=8, label=labels)

        elif plot_type == "bar":
            color = style.get("color", "steelblue")
            alpha = style.get("alpha", 0.7)
            bars = ax.bar(x, y, color=color, alpha=alpha, label=labels)

            # Add value labels on bars if requested
            if style.get("show_values", True):
                for i, (xi, yi) in enumerate(zip(x, y)):
                    ax.text(i, yi + max(y) * 0.01, f'{yi:.1f}',
                           ha='center', va='bottom', fontsize=9)

        elif plot_type == "scatter":
            color = style.get("color", "steelblue")
            alpha = style.get("alpha", 0.6)
            size = style.get("size", 50)
            ax.scatter(x, y, c=color, alpha=alpha, s=size, label=labels)

    elif plot_type in ["heatmap", "contour"]:
        z = np.array(data.get("z", [[]]))
        x = data.get("x", None)
        y = data.get("y", None)

        if plot_type == "heatmap":
            cmap = style.get("cmap", "RdYlBu_r")
            im = ax.imshow(z, cmap=cmap, aspect='auto', origin='lower')
            plt.colorbar(im, ax=ax, label=style.get("colorbar_label", ""))

            # Set tick labels if x and y provided
            if x is not None:
                ax.set_xticks(range(len(x)))
                ax.set_xticklabels(x, rotation=45)
            if y is not None:
                ax.set_yticks(range(len(y)))
                ax.set_yticklabels(y)

        elif plot_type == "contour":
            cmap = style.get("cmap", "RdYlBu_r")
            levels = style.get("levels", 10)
            if x is not None and y is not None:
                contour = ax.contourf(x, y, z, levels=levels, cmap=cmap)
            else:
                contour = ax.contourf(z, levels=levels, cmap=cmap)
            plt.colorbar(contour, ax=ax, label=style.get("colorbar_label", ""))

    # Set labels and title
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)

    # Add grid
    if style.get("grid", True):
        ax.grid(True, alpha=0.3)

    # Add legend if labels provided
    if data.get("labels") is not None or style.get("legend"):
        ax.legend()

    # Add metadata annotation if provided
    metadata = style.get("metadata", {})
    if metadata:
        metadata_text = ""

        # Build metadata text
        if "location" in metadata:
            metadata_text += f"Location: {metadata['location']}\n"
        if "coordinates" in metadata:
            metadata_text += f"Coordinates: {metadata['coordinates']}\n"
        if "scenario" in metadata:
            metadata_text += f"Scenario: {metadata['scenario']}\n"
        if "year" in metadata or "time_range" in metadata:
            time_info = metadata.get('year') or metadata.get('time_range')
            metadata_text += f"Time: {time_info}\n"
        if "ensemble" in metadata:
            metadata_text += f"Ensemble: {metadata['ensemble']}\n"
        if "variable" in metadata:
            metadata_text += f"Variable: {metadata['variable']}\n"
        if "source" in metadata:
            metadata_text += f"Source: {metadata['source']}\n"

        # Add any additional metadata
        for key, value in metadata.items():
            if key not in ["location", "coordinates", "scenario", "year", "time_range",
                          "ensemble", "variable", "source"]:
                metadata_text += f"{key}: {value}\n"

        # Add metadata box to plot
        if metadata_text:
            ax.text(0.02, 0.98, metadata_text.strip(),
                   transform=ax.transAxes,
                   fontsize=9,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                   family='monospace')

    plt.tight_layout()
    return fig


def plot_climate_data(
    plot_config: str | Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main function called by the model to create plots.

    Args:
        plot_config: JSON string or dict containing plot configuration

    Returns:
        Dictionary with status and figure object
    """
    try:
        # Parse configuration - handle both string and dict inputs
        if isinstance(plot_config, dict):
            config = plot_config
        else:
            config = json.loads(plot_config)

        # Create the plot
        fig = create_plot(
            plot_type=config.get("plot_type", "line"),
            data=config.get("data", {}),
            title=config.get("title", ""),
            xlabel=config.get("xlabel", ""),
            ylabel=config.get("ylabel", ""),
            style=config.get("style", {})
        )

        return {
            "status": "ok",
            "figure": fig,
            "message": "Plot created successfully"
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to create plot: {str(e)}"
        }
