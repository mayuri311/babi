from nicegui import ui
import time
from fontTools.ttLib import TTFont
from PIL import ImageFont
from nicegui.element import Element

ui.add_css(f"""
@font-face {{
    font-family: 'AmaticSC';
    src: url('/static/font-amatic-sc-0.0.4/font_amatic_sc/files/AmaticSC-Bold.ttf');
}}
""")


# Create a placeholder for the event log
event_log = ui.column().style('max-height: 200px; overflow-y: auto; position: absolute; bottom: 40px; left: 20px; right: 20px;')

def log_event(message, color="blue"):
    """Logs an event in the UI."""
    with event_log:
        ui.label(message).style(f'background-color: rgba(230, 230, 230, 0.7); color: rgba(100, 100, 100, 1); font-family: "AmaticSC"; font-size: 16px; margin-bottom: 8px; padding: 10px 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
    if sound:
        ui.run_javascript(f'playSound("{sound}");')
def simulate_crying():
    log_event("🚨Baby is crying!", "red")
    ui.notify("Baby is crying!", color= "#red", position="top-right")  # Top-right position for notification

def simulate_danger():
    log_event("⚠️ Baby near a danger zone!", "orange")
    ui.notify("Danger detected!", color="orange", position="top-right")  # Top-right position for notification

def simulate_motion():
    log_event("📹 Motion detected!", "green")
    ui.notify("Motion detected!", color="green", position="top-right")  # Top-right position for notification

def clear_log():
    """Clears the event log."""
    event_log.clear()

# Create a menu bar (top left corner)
ui.row().style('width: 100%; height: 100px; position: absolute; top: 0; left: 0; background-color: #ddd3e4; padding: 10px; border-radius: 5px; z-index: 1;')
    # menu_button = ui.button('☰ Menu').style('font-size: 18px; color: white; background-color: #333; border: none;')

ui.image('logo2.png').style('width: 175px; height: 55px; position: absolute; top: 60; left: 0; background-color: #ddd3e4; padding: 10px; border-radius: 5px; z-index: 1;')

# Element('img') \
#     .props('src=logo2.png') \
#     .style('width: 200px; height: 200px; border: 1pt solid gray; object-fit:scale-down')

# Create the toolbar (hidden by default)
# toolbar = ui.column().style('position: absolute; top: 60px; left: 0; width: 200px; background-color: #f4f4f4; padding: 10px; border-radius: 5px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); display: none;')


# ui.button('Simulate Baby Crying', on_click=simulate_crying, color="#6a89a7").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; width: 100%; margin-bottom: 10px;')
# ui.button('Simulate Danger Zone Alert', on_click=simulate_danger, color="#6a89a7").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; width: 100%; margin-bottom: 10px;')
# ui.button('Simulate Motion Detection', on_click=simulate_motion, color="#6a89a7").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; width: 100%; margin-bottom: 10px;')
# ui.button('Clear Event Log', on_click=clear_log, color="gray").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; width: 100%; margin-bottom: 10px;')

# Toggle function for the toolbar
# def toggle_toolbar():
#     ui.run_javascript("""
#         let toolbar = document.getElementById('toolbar');
#         if (toolbar.style.display === 'none' || toolbar.style.display === '') {
#             toolbar.style.display = 'block';
#         } else {
#             toolbar.style.display = 'none';
#         }
#     """)

# menu_button.on('click', toggle_toolbar)

# UI Layout with background
# with ui.row().style('width: 85px; height: 85px; background-color: #c791db; padding: 10px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); position: absolute; top: 10px; left: 20px; z-index: 9999;'):
#     ui.label('bAbI').style('font-family: "AmaticSC"; font-size: 30px; font-weight: bold; color: #FFF; text-align: center;')# Add a placeholder for the live camera feed (horizontal box)
# ui.image('https://app.brandmark.io/v3/#logo_data=%7B%22id%22%3A%22logo-5dfbea2a-c11e-416b-b5c1-b6bdd067cbea%22%2C%22layout%22%3A1%2C%22title%22%3A%22babi%22%2C%22titleFamily%22%3A%22Brandmark%20Serif%206%22%2C%22titleVariant%22%3A%22regular%22%2C%22titleColor%22%3A%5B%7B%22hex%22%3A%22%23c791db%22%2C%22location%22%3A0%7D%2C%7B%22hex%22%3A%22%23971efc%22%2C%22location%22%3A0.25%7D%2C%7B%22hex%22%3A%22%23971efc%22%2C%22location%22%3A0.5%7D%2C%7B%22hex%22%3A%22%23ddd3e4%22%2C%22location%22%3A0.75%7D%2C%7B%22hex%22%3A%22%23971efc%22%2C%22location%22%3A1%7D%5D%2C%22titleScale%22%3A2.5%2C%22titleLetterSpace%22%3A0%2C%22titleLineSpace%22%3A1.1%2C%22titleBoldness%22%3A0%2C%22titleX%22%3A0%2C%22titleY%22%3A0%2C%22titleAlign%22%3A%22center%22%2C%22slogan%22%3A%22%22%2C%22sloganFamily%22%3A%22Lora%22%2C%22sloganVariant%22%3A%22italic%22%2C%22sloganColor%22%3A%5B%7B%22hex%22%3A%22%23971efc%22%7D%5D%2C%22sloganScale%22%3A2.5%2C%22sloganLetterSpace%22%3A0%2C%22sloganLineSpace%22%3A1.1%2C%22sloganBoldness%22%3A0%2C%22sloganAlign%22%3A%22center%22%2C%22sloganX%22%3A0%2C%22sloganY%22%3A0%2C%22icon%22%3A%7B%22id%22%3A%2224381%22%2C%22type%22%3A%22noun%22%2C%22preview%22%3A%22https%3A%2F%2Fapp.brandmark.io%2Fnounpreview%2F24381.png%22%7D%2C%22showIcon%22%3Atrue%2C%22iconScale%22%3A1%2C%22iconColor%22%3A%5B%7B%22hex%22%3A%22%23971efc%22%7D%5D%2C%22iconContainer%22%3Anull%2C%22showIconContainer%22%3Afalse%2C%22iconContainerScale%22%3A1%2C%22iconContainerColor%22%3A%5B%7B%22hex%22%3A%22%23e2d3fc%22%7D%5D%2C%22iconSpace%22%3A1%2C%22iconX%22%3A0%2C%22iconY%22%3A0%2C%22nthChar%22%3A0%2C%22container%22%3Anull%2C%22showContainer%22%3Afalse%2C%22containerScale%22%3A1%2C%22containerColor%22%3A%5B%7B%22hex%22%3A%22%23e2d3fc%22%7D%5D%2C%22containerX%22%3A0%2C%22containerY%22%3A0%2C%22backgroundColor%22%3A%5B%7B%22hex%22%3A%22%23fcfcfc%22%7D%5D%2C%22palette%22%3A%5B%22%23fcfcfc%22%2C%22%23971efc%22%2C%22%239f3ffc%22%2C%22%23a760fc%22%2C%22%23af82fd%22%5D%2C%22keywords%22%3A%5B%22baby%22%2C%22kindness%22%2C%22watchful%22%2C%22soft%22%2C%22caring%22%5D%7D')
camera_placeholder = ui.row().style('width: 100%; height: 400px; background-color: #dcdcdc; margin-top: 100px; margin-bottom: 20px; border-radius: 15px; justify-content: center; align-items: center;')
with camera_placeholder:
    ui.label("🔴 Live Camera Feed Placeholder").style('font-size: 24px; font-weight: bold; color: #333;')

# Buttons for Simulated Events with improved style
with ui.row().style('gap: 15px; justify-content: center; margin-top: 40px;'):
    ui.button('Simulate Baby Crying', on_click=simulate_crying, color="#c791db").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
    ui.button('Simulate Danger Zone Alert', on_click=simulate_danger, color="#c791db").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
    ui.button('Simulate Motion Detection', on_click=simulate_motion, color="#c791db").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
    ui.button('Clear Event Log', on_click=clear_log, color="gray").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')

# Start the app
ui.run()