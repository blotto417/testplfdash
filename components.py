import streamlit as st
import re

def kpi_card(
    title: str,
    value: int,
    percent: float,
    percent_label: str,
    bar_value: int,
    bar_max: int,
    bar_color: str = "#FFA940",
    bar_bg_color: str = "#3A47A8",
    card_bg_color: str = "#001DBA",
    text_color: str = "#FFFFFF",
    percent_color: str = "#FFA940",
    width: str = "100%",
    height: str = "12vw",
    bar_text_position: str = "right",  # 'right', 'left', 'center', 'none'
):
    """
    Streamlit KPI card component with customizable colors, responsive width (100% of parent) and height (12vw by default), and bar text position.
    Bar and font sizes scale automatically with card height, with more aggressive scaling for small cards.
    """
    percent_display = f"{percent:.1f}%"
    bar_percent = min(max(bar_value / bar_max, 0), 1) if bar_max else 0
    bar_width = int(bar_percent * 100)

    # Parse height for scaling
    card_height_px = 170  # fallback
    m = re.match(r"([\d.]+)(px|vw|vh)?", height.strip())
    if m:
        val, unit = m.group(1), m.group(2)
        try:
            val = float(val)
            if unit == "px" or unit is None:
                card_height_px = int(val)
            elif unit == "vw":
                card_height_px = int(val * 0.01 * 1200)
            elif unit == "vh":
                card_height_px = int(val * 0.01 * 800)
        except Exception:
            pass

    # Responsive scaling
    if card_height_px < 100:
        bar_height = max(8, int(card_height_px * 0.16))
        value_font = max(10, int(card_height_px * 0.22))
        label_font = max(8, int(card_height_px * 0.09))
        percent_font = max(8, int(card_height_px * 0.11))
        bar_text_font = max(8, int(card_height_px * 0.10))
    else:
        bar_height = max(12, int(card_height_px * 0.10))
        value_font = max(14, int(card_height_px * 0.15))
        label_font = max(10, int(card_height_px * 0.10))
        percent_font = max(10, int(card_height_px * 0.08))
        bar_text_font = max(10, int(card_height_px * 0.08))

    # Bar text
    bar_text_html = ""
    if bar_text_position == "right":
        bar_text_html = f'<div class="bar-label" style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%); font-size: {bar_text_font}px; color: {text_color}; opacity: 0.85; font-weight: 500;">{bar_max:,}</div>'
    elif bar_text_position == "left":
        bar_text_html = f'<div class="bar-label" style="position: absolute; left: 8px; top: 50%; transform: translateY(-50%); font-size: {bar_text_font}px; color: {text_color}; opacity: 0.85; font-weight: 500;">{bar_max:,}</div>'
    elif bar_text_position == "center":
        bar_text_html = f'<div class="bar-label" style="position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); font-size: {bar_text_font}px; color: {text_color}; opacity: 0.85; font-weight: 500;">{bar_max:,}</div>'

    # Optional responsive CSS
    style_block = """
    <style>
    @media screen and (max-width: 768px) {
        .kpi-card .label { font-size: 0.75em !important; }
        .kpi-card .value { font-size: 1.2em !important; }
        .kpi-card .percent { font-size: 0.9em !important; }
        .kpi-card .bar-label { font-size: 0.8em !important; }
    }
    </style>
    """
    st.markdown(style_block, unsafe_allow_html=True)

    # KPI Card HTML
    card_html = f'''
    <div class="kpi-card" style="background: {card_bg_color}; color: {text_color}; border-radius: 10px; padding: 1rem; width: {width}; max-width: 100%; min-width: 180px; height: {height}; min-height: 50px; display: flex; flex-direction: column; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow: hidden;">
        <div style="flex: 1 1 auto; display: flex; flex-direction: column; justify-content: center; align-items: center; min-width: 0; min-height: 0;">
            <div class="label" style="font-size: {label_font}px; opacity: 0.85; text-align: center;">{title}</div>
            <div class="value" style="font-size: {value_font}px; font-weight: 700; margin: 4px 0; letter-spacing: 1px; text-align: center;">{value:,}</div>
            <div class="percent" style="font-size: {percent_font}px; text-align: center;">
                <span style="color: {percent_color}; font-weight: 600;">{percent_display}</span>
                <span style="opacity: 0.85;"> {percent_label}</span>
            </div>
        </div>
        <div style="width: 100%; flex-shrink: 0;">
            <div style="position: relative; height: {bar_height}px; background: {bar_bg_color}; border-radius: {int(bar_height/2)}px;">
                <div style="position: absolute; left: 0; top: 0; height: {bar_height}px; width: {bar_width}%; background: {bar_color}; border-radius: {int(bar_height/2)}px; transition: width 0.5s;"></div>
                {bar_text_html}
            </div>
        </div>
    </div>
    '''
    st.markdown(card_html, unsafe_allow_html=True)

# def styled_metric_card_with_bar(
#     title: str,
#     value: str,
#     delta: str = None,
#     bar_value: float = 0.0,
#     bar_max: float = 100.0,
#     background_color: str = "#FFF",
#     border_size_px: int = 1,
#     border_color: str = "#CCC",
#     border_radius_px: int = 5,
#     border_left_color: str = "#9AD8E1",
#     box_shadow: bool = True,
#     bar_color: str = "#9AD8E1",
#     bar_bg_color: str = "#E9ECEF",
#     bar_height_px: int = 6,
#     show_bar_text: bool = True,
#     bar_text_position: str = "right",  # 'right', 'left', 'center', 'none'
#     width: str = "100%",
#     height: str = "140px",
# ):
#     """
#     Creates a styled metric card with a progress bar, similar to st.metric but with custom styling and a bar.
    
#     Args:
#         title (str): The metric title
#         value (str): The main metric value
#         delta (str, optional): The delta value (change indicator). Defaults to None.
#         bar_value (float): Current value for the progress bar. Defaults to 0.0.
#         bar_max (float): Maximum value for the progress bar. Defaults to 100.0.
#         background_color (str): Background color of the card. Defaults to "#FFF".
#         border_size_px (int): Border size in pixels. Defaults to 1.
#         border_color (str): Border color. Defaults to "#CCC".
#         border_radius_px (int): Border radius in pixels. Defaults to 5.
#         border_left_color (str): Left border accent color. Defaults to "#9AD8E1".
#         box_shadow (bool): Whether to apply box shadow. Defaults to True.
#         bar_color (str): Color of the progress bar fill. Defaults to "#9AD8E1".
#         bar_bg_color (str): Color of the progress bar background. Defaults to "#E9ECEF".
#         bar_height_px (int): Height of the progress bar in pixels. Defaults to 6.
#         show_bar_text (bool): Whether to show text on the bar. Defaults to True.
#         bar_text_position (str): Position of bar text ('right', 'left', 'center', 'none'). Defaults to "right".
#         width (str): Width of the card. Defaults to "100%".
#         height (str): Height of the card. Defaults to "auto".
#     """
    
#     # Calculate bar percentage
#     bar_percent = min(max(bar_value / bar_max, 0), 1) if bar_max else 0
#     bar_width = int(bar_percent * 100)
    
#     # Box shadow string
#     box_shadow_str = (
#         "box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;"
#         if box_shadow
#         else "box-shadow: none !important;"
#     )
    
#     # Bar text HTML
#     bar_text_html = ""
#     if show_bar_text and bar_text_position != "none":
#         text_style = f"position: absolute; top: 50%; transform: translateY(-50%); font-size: 0.75rem; color: #6C757D; font-weight: 500;"
#         if bar_text_position == "right":
#             bar_text_html = f'<div style="{text_style} right: 8px;">{bar_max:,.0f}</div>'
#         elif bar_text_position == "left":
#             bar_text_html = f'<div style="{text_style} left: 8px;">{bar_max:,.0f}</div>'
#         elif bar_text_position == "center":
#             bar_text_html = f'<div style="{text_style} left: 50%; transform: translate(-50%, -50%);">{bar_max:,.0f}</div>'
    
#     # Delta HTML
#     delta_html = ""
#     if delta:
#         delta_color = "#28A745" if delta.startswith("+") else "#DC3545" if delta.startswith("-") else "#6C757D"
#         delta_html = f'<div style="font-size: 0.875rem; color: {delta_color}; font-weight: 500;">{delta}</div>'
    
#     # Create the styled metric card HTML
#     card_html = f"""
#     <div style="
#         background-color: {background_color};
#         border: {border_size_px}px solid {border_color};
#         padding: 1rem;
#         border-radius: {border_radius_px}px;
#         border-left: 0.5rem solid {border_left_color} !important;
#         {box_shadow_str}
#         width: {width};
#         height: {height};
#         display: flex;
#         flex-direction: column;
#         justify-content: space-between;
#     ">
#         <div style="flex: 1;">
#             <div style="font-size: 0.875rem; color: #6C757D; margin-bottom: 0.5rem;">{title}</div>
#             <div style="font-size: 1.5rem; font-weight: 700; color: #212529; margin-bottom: 0.25rem;">{value}</div>
#             {delta_html}
#         </div>
#         <div style="margin-top: 1rem;">
#             <div style="position: relative; height: {bar_height_px}px; background: {bar_bg_color}; border-radius: {int(bar_height_px/2)}px; overflow: hidden;">
#                 <div style="position: absolute; left: 0; top: 0; height: 100%; width: {bar_width}%; background: {bar_color}; border-radius: {int(bar_height_px/2)}px; transition: width 0.3s ease-in-out;"></div>
#                 {bar_text_html}
#             </div>
#         </div>
#     </div>
#     """
    
#     st.markdown(card_html, unsafe_allow_html=True)


import streamlit as st

def styled_metric_card_with_bar(
    title: str,
    value: str,
    delta: str = None,
    bar_value: float = 0.0,
    bar_max: float = 100.0,
    background_color: str = "#FFF",
    border_size_px: int = 1,
    border_color: str = "#CCC",
    border_radius_px: int = 5,
    border_left_color: str = "#9AD8E1",
    box_shadow: bool = True,
    bar_color: str = "#9AD8E1",
    bar_bg_color: str = "#E9ECEF",
    bar_height_px: int = 6,
    show_bar_text: bool = True,
    show_bar: bool = True,
    bar_text_position: str = "right",  # 'right', 'left', 'center', 'none'
    width: str = "100%",
    height: str = "140px",
):
    """
    Creates a styled metric card with a progress bar, similar to st.metric but with custom styling and a bar.
    
    Args:
        title (str): The metric title
        value (str): The main metric value
        delta (str, optional): The delta value (change indicator). Defaults to None.
        bar_value (float): Current value for the progress bar. Defaults to 0.0.
        bar_max (float): Maximum value for the progress bar. Defaults to 100.0.
        background_color (str): Background color of the card. Defaults to "#FFF".
        border_size_px (int): Border size in pixels. Defaults to 1.
        border_color (str): Border color. Defaults to "#CCC".
        border_radius_px (int): Border radius in pixels. Defaults to 5.
        border_left_color (str): Left border accent color. Defaults to "#9AD8E1".
        box_shadow (bool): Whether to apply box shadow. Defaults to True.
        bar_color (str): Color of the progress bar fill. Defaults to "#9AD8E1".
        bar_bg_color (str): Color of the progress bar background. Defaults to "#E9ECEF".
        bar_height_px (int): Height of the progress bar in pixels. Defaults to 6.
        show_bar_text (bool): Whether to show text on the bar. Defaults to True.
        bar_text_position (str): Position of bar text ('right', 'left', 'center', 'none'). Defaults to "right".
        width (str): Width of the card. Defaults to "100%".
        height (str): Height of the card. Defaults to "auto".
    """
    
    # Calculate bar percentage
    bar_percent = min(max(bar_value / bar_max, 0), 1) if bar_max else 0
    bar_width = int(bar_percent * 100)
    
    # Box shadow string
    box_shadow_str = (
        "box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;"
        if box_shadow
        else "box-shadow: none !important;"
    )
    
    # Bar text HTML
    bar_text_html = ""
    if show_bar_text and bar_text_position != "none":
        text_style = f"position: absolute; top: 50%; transform: translateY(-50%); font-size: 0.75rem; color: #6C757D; font-weight: 500;"
        if bar_text_position == "right":
            bar_text_html = f'<div style="{text_style} right: 8px;">{bar_max:,.0f}</div>'
        elif bar_text_position == "left":
            bar_text_html = f'<div style="{text_style} left: 8px;">{bar_max:,.0f}</div>'
        elif bar_text_position == "center":
            bar_text_html = f'<div style="{text_style} left: 50%; transform: translate(-50%, -50%);">{bar_max:,.0f}</div>'
    # Delta HTML
    delta_html = ""
    if delta:
        delta_color = "#28A745" if delta.startswith("+") else "#DC3545" if delta.startswith("-") else "#6C757D"
        delta_html = f'<div style="font-size: 0.875rem; color: {delta_color}; font-weight: 500;">{delta}</div>'
    if show_bar:
    # Create the styled metric card HTML
        card_html = f"""
        <div style="
            background-color: {background_color};
            border: {border_size_px}px solid {border_color};
            padding: 1rem;
            border-radius: {border_radius_px}px;
            border-left: 0.5rem solid {border_left_color} !important;
            {box_shadow_str}
            width: {width};
            height: {height};
            max-height: {height};
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div style="flex: 1;">
                <div style="font-size: 0.875rem; color: #6C757D; margin-bottom: 0.5rem;">{title}</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #212529; margin-bottom: 0.25rem;">{value}</div>
                {delta_html}
            </div>
            <div style="margin-top: 1rem;">
                <div style="position: relative; height: {bar_height_px}px; background: {bar_bg_color}; border-radius: {int(bar_height_px/2)}px; overflow: hidden;">
                    <div style="position: absolute; left: 0; top: 0; height: 100%; width: {bar_width}%; background: {bar_color}; border-radius: {int(bar_height_px/2)}px; transition: width 0.3s ease-in-out;"></div>
                    {bar_text_html}
                </div>
            </div>
        </div>
        """
    else:
        card_html = f"""
        <div style="
            background-color: {background_color};
            border: {border_size_px}px solid {border_color};
            padding: 1rem;
            border-radius: {border_radius_px}px;
            border-left: 0.5rem solid {border_left_color} !important;
            {box_shadow_str}
            width: {width};
            height: {height};
            max-height: {height};
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div style="flex: 1;">
                <div style="font-size: 0.875rem; color: #6C757D; margin-bottom: 0.5rem;">{title}</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #212529; margin-bottom: 0.25rem;">{value}</div>
            </div>
        </div>
        """
    
    st.markdown(card_html, unsafe_allow_html=True)

def vmk_header_container(title, icon="📊", key_suffix=""):
    """
    Creates a VMK-styled header container with dark background and title
    
    Args:
        title (str): The title text to display
        icon (str): Icon to display (emoji or text)
        key_suffix (str): Suffix for unique container key
    """
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%);
            padding: 1rem 1.5rem;
            border-radius: 12px 12px 0 0;
            margin-bottom: 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border: 1px solid #34495E;
            position: relative;
            overflow: hidden;
        ">
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: relative;
                z-index: 2;
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                ">
                    <span style="
                        font-size: 1.5rem;
                        filter: brightness(1.2);
                    ">{icon}</span>
                    <h2 style="
                        color: #FFFFFF;
                        margin: 0;
                        font-size: 1.4rem;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    ">{title}</h2>
                </div>
                <div style="
                    color: #BDC3C7;
                    font-size: 1.2rem;
                    opacity: 0.8;
                ">🌙</div>
            </div>
            <div style="
                position: absolute;
                top: 0;
                right: 0;
                width: 100px;
                height: 100%;
                background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.05) 100%);
                pointer-events: none;
            "></div>
        </div>
        """,
        unsafe_allow_html=True
    )

def vmk_data_container(key_suffix=""):
    """
    Creates a VMK-styled data container with a light background and border
    
    Args:
        key_suffix (str): Suffix for unique container key
    """
    return st.container(border=True)

def styled_kpi_card(
    title: str,
    value: str,
    delta: str = "",
    icon: str = "📊",
    bg_color: str = "#FFFFFF",
    border_color: str = "#E0E0E0",
    icon_bg_color: str = "#F0F4F8",
    icon_color: str = "#007BFF",
    height: str = "150px"
):
    """
    Creates a modern, visually appealing metric card with an icon.
    """
    card_html = f"""
    <div style="
        background-color: {bg_color};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 1.5rem;
        height: {height};
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: all 0.3s ease-in-out;
    ">
        <div style="display: flex; align-items: flex-start; justify-content: space-between;">
            <div style="
                width: 48px;
                height: 48px;
                border-radius: 50%;
                background-color: {icon_bg_color};
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                color: {icon_color};
            ">
                {icon}
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1rem; color: #6C757D;">{title}</div>
                <div style="font-size: 2rem; font-weight: 700; color: #212529;">{value}</div>
            </div>
        </div>
        <div style="font-size: 0.875rem; color: #6C757D; margin-top: 1rem;">
            {delta}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def styled_kpi_card(
    title: str,
    value: str,
    delta: str = "",
    icon: str = "📊",
    progress_value: float = 0,
    progress_max: float = 100,
    color: str = "blue"
):
    """
    A modern, visually rich KPI card with an icon and a progress bar.
    """
    
    color_map = {
        "blue": {"bg": "#E6F3FF", "icon": "#007BFF", "progress": "#007BFF"},
        "green": {"bg": "#E6F9F0", "icon": "#28A745", "progress": "#28A745"},
        "orange": {"bg": "#FFF4E6", "icon": "#FD7E14", "progress": "#FD7E14"},
        "red": {"bg": "#FFE6E6", "icon": "#DC3545", "progress": "#DC3545"}
    }
    theme = color_map.get(color, color_map["blue"])
    
    progress_percentage = min((progress_value / progress_max) * 100, 100) if progress_max > 0 else 0
    
    st.markdown(f"""
    <div class="metric-card" style="
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        height: 170px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        <div style="display: flex; align-items: flex-start; justify-content: space-between;">
            <div style="
                width: 48px;
                height: 48px;
                border-radius: 12px;
                background-color: {theme['bg']};
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                color: {theme['icon']};
            ">
                {icon}
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1rem; color: #6C757D; font-weight: 500;">{title}</div>
                <div style="font-size: 2.2rem; font-weight: 700; color: #212529;">{value}</div>
            </div>
        </div>
        <div>
            <div style="font-size: 0.9rem; color: #6C757D; margin-bottom: 0.5rem;">{delta}</div>
            <div style="background-color: #E9ECEF; border-radius: 4px; height: 8px;">
                <div style="
                    width: {progress_percentage}%;
                    background-color: {theme['progress']};
                    border-radius: 4px;
                    height: 8px;
                "></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
