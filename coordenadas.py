from pynput import mouse, keyboard

def on_click(x, y, button, pressed):
    if pressed:
        print(f"🖱️ Clique detectado - Coordenadas: ({x}, {y})")

def on_move(x, y):
    print(f"📍 Mouse em: ({x}, {y})", end="\r")

def on_press(key):
    if key == keyboard.Key.esc:
        print("\n🚪 Saindo...")
        return False

print("🎯 Mova o mouse e clique para capturar coordenadas.")
print("🔴 Pressione ESC para sair.\n")

with mouse.Listener(on_click=on_click, on_move=on_move) as mouse_listener, \
     keyboard.Listener(on_press=on_press) as keyboard_listener:
    mouse_listener.join()
    keyboard_listener.join()
