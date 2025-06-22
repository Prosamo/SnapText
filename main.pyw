import tkinter, sys, os
import pyautogui
import numpy as np
import cv2
import pytesseract
import pyperclip
from PIL import Image, ImageTk

# ドラッグ開始した時のイベント - - - - - - - - - - - - - - - - - - - - - - - - - - 
def start_point_get(event):
    global start_x, start_y # グローバル変数に書き込みを行なうため宣言

    canvas1.delete("rect1")  # すでに"rect1"タグの図形があれば削除

    # canvas1上に四角形を描画（rectangleは矩形の意味）
    canvas1.create_rectangle(event.x,
                             event.y,
                             event.x + 1,
                             event.y + 1,
                             outline="red",
                             width = 3,
                             tag="rect1")
    # グローバル変数に座標を格納
    start_x, start_y = event.x, event.y

# ドラッグ中のイベント - - - - - - - - - - - - - - - - - - - - - - - - - - 
def rect_drawing(event):

    # ドラッグ中のマウスポインタが領域外に出た時の処理
    if event.x < 0:
        end_x = 0
    else:
        end_x = min(img_resized.width, event.x)
    if event.y < 0:
        end_y = 0
    else:
        end_y = min(img_resized.height, event.y)

    # "rect1"タグの画像を再描画
    canvas1.coords("rect1", start_x, start_y, end_x, end_y)

# ドラッグを離したときのイベント - - - - - - - - - - - - - - - - - - - - - - - - - - 
def release_action(event):
    global region  # グローバル変数に書き込みを行なうため宣言
    # "rect1"タグの画像の座標を元の縮尺に戻して取得
    start_x, start_y, end_x, end_y = [
        round(n * RESIZE_RETIO) for n in canvas1.coords("rect1")
    ]

    # 画面領域のスクリーンショット取得（画像を保存せずに処理）
    region = [start_x, start_y, end_x, end_y]  # 選択した領域の座標
    
def press_enter(event):
    extract_text(*region)
    # 選択した領域の座標をファイルに保存
    with open("region.txt", "w") as f:
        f.write(",".join(map(str, region)))
    sys.exit()

def extract_text(x1, y1, x2, y2):
    screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))

    image = prepare_image(screenshot)
    # OCRで文字を抽出
    text = pytesseract.image_to_string(image, lang='jpn')
    text = text.replace(" ", "")
    # クリップボードへコピー
    pyperclip.copy(text)

    pyautogui.alert("抽出した文字をクリップボードへコピーしました。画像は保存されません。")

    print(text)

def prepare_image(img):
    # スクリーンショットを保存せずに処理
    img_arr = np.array(img)  # numpy配列に変換
    img_data = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)  # OpenCV形式に変換
    # グレースケール化
    gray_img = cv2.cvtColor(img_data, cv2.COLOR_BGR2GRAY)
    # ノイズ除去
    denoised_img = cv2.bilateralFilter(gray_img, 9, 75, 75)
    # 二値化処理
    _, binary_img = cv2.threshold(denoised_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary_img

# メイン処理 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if __name__ == "__main__":
    RESIZE_RETIO = 1 # 縮小倍率の規定
    
    if os.path.exists("region.txt"):
        with open("region.txt", "r") as f:
            region = list(map(int, f.read().strip().split(",")))
    else:
        region = [100, 100, 200, 200]

    # 表示する画像の取得（スクリーンショット）
    img = pyautogui.screenshot()
    # 好みのサイズに画像リサイズ
    img_resized = img.resize(size=(int(img.width / RESIZE_RETIO),
                                   int(img.height / RESIZE_RETIO)),
                             resample=Image.BILINEAR)

    root = tkinter.Tk()
    root.attributes("-fullscreen", True)  # tkinterウィンドウをフルスクリーンに設定
    root.attributes("-topmost", True) # tkinterウィンドウを常に最前面に表示
    root.focus_force()  # tkinterウィンドウにフォーカスを設定

    # tkinterで表示できるように画像変換
    img_tk = ImageTk.PhotoImage(img_resized)

    # Canvasウィジェットの描画
    canvas1 = tkinter.Canvas(root,
                             bg="black",
                             width=img_resized.width,
                             height=img_resized.height)
    # Canvasウィジェットに取得した画像を描画
    canvas1.create_image(0, 0, image=img_tk, anchor=tkinter.NW)
    canvas1.config(cursor="cross")
    # canvas1上に四角形を描画（rectangleは矩形の意味）
    canvas1.create_rectangle(region[0],
                             region[1],
                             region[2],
                             region[3],
                             outline="red",
                             width = 3,
                             tag="rect1")

    # Canvasウィジェットを配置し、各種イベントを設定
    canvas1.pack()
    canvas1.bind("<ButtonPress-1>", start_point_get)
    canvas1.bind("<Button1-Motion>", rect_drawing)
    canvas1.bind("<ButtonRelease-1>", release_action)
    root.bind("<Return>", press_enter)  # EnterキーでOCR実行
    root.bind("<Escape>", sys.exit)  # Escapeキーで終了

    root.mainloop()