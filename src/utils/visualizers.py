import os
import streamlit as st
import matplotlib.pyplot as plt
import gdstk
from vcdvcd import VCDVCD
import numpy as np

def render_waveform(vcd_path):
    """Parses VCD and renders a step plot using Matplotlib."""
    try:
        vcd = VCDVCD(vcd_path)
        signals = vcd.get_signals()
        
        if not signals:
            st.warning("No signals found in VCD.")
            return

        # Filter signals to avoid clutter (e.g., top 10)
        # Prefer signals in the top module
        display_signals = [s for s in signals if "tb" in s or "clk" in s or "rst" in s][:15]
        if not display_signals:
            display_signals = signals[:15]

        fig, ax = plt.subplots(len(display_signals), 1, figsize=(10, len(display_signals) * 0.8), sharex=True)
        if len(display_signals) == 1:
            ax = [ax]

        endtime = vcd.endtime
        
        for i, sig_name in enumerate(display_signals):
            sig = vcd[sig_name]
            tv = sig.tv # List of (time, value)
            
            times = [t for t, v in tv]
            values = []
            for t, v in tv:
                if v == '0': values.append(0)
                elif v == '1': values.append(1)
                else: values.append(0.5) # X or Z
            
            # Add end time point for step plot continuity
            times.append(endtime)
            values.append(values[-1])
            
            ax[i].step(times, values, where='post')
            ax[i].set_ylabel(sig_name.split('.')[-1], rotation=0, ha='right', fontsize=8)
            ax[i].set_yticks([0, 1])
            ax[i].set_yticklabels(['0', '1'], fontsize=6)
            ax[i].grid(True, alpha=0.3)
            
            # Remove spines for cleaner look
            ax[i].spines['top'].set_visible(False)
            ax[i].spines['right'].set_visible(False)
            ax[i].spines['bottom'].set_visible(False)
            if i != len(display_signals) - 1:
                ax[i].set_xticks([])

        ax[-1].set_xlabel("Time (ns)")
        plt.tight_layout()
        st.pyplot(fig)
        
    except Exception as e:
        st.error(f"Failed to render Waveform: {e}")

def render_gds(gds_path):
    """Renders GDS to SVG using gdstk and displays it."""
    try:
        # Check if file exists and is not empty
        if os.path.getsize(gds_path) == 0:
            st.warning("GDS file is empty.")
            return

        lib = gdstk.read_gds(gds_path)
        top_cells = lib.top_level()
        if not top_cells:
            st.error("No top level cell found in GDS.")
            return
            
        cell = top_cells[0]
        
        # Create a temporary SVG path
        svg_path = gds_path + ".svg"
        cell.write_svg(svg_path)
        
        # Display
        st.image(svg_path, caption=f"Layout: {os.path.basename(gds_path)}")
        
    except Exception as e:
        st.error(f"Failed to render GDS: {e}")
