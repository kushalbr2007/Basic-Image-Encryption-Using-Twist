import math
import random
from PIL import Image
from ics_images import *

# --- RSA FUNCTIONS ---
def gcd(a, b):
    while b > 0: a, b = b, a % b
    return a

def GenN():
    Prime1, Prime2 = 73, 97
    N = Prime1 * Prime2
    N_1 = (Prime1 - 1) * (Prime2 - 1)
    e = random.randint(2, N_1)
    while gcd(e, N_1) != 1:
        e = random.randint(2, N_1)
    return N, e

def LockM(M, e, N):
    return pow(M, e, N)

def UnlockM(Locked_Message, e):
    Prime1, Prime2 = 73, 97
    N_1 = (Prime1 - 1) * (Prime2 - 1)
    d = pow(e, -1, N_1) 
    return pow(Locked_Message, d, Prime1 * Prime2)

# --- ANTI-BLUR SAMPLING ---
def get_smooth_pixel(pixels, x, y, w, h):
    x_int, y_int = int(math.floor(x)), int(math.floor(y))
    if x_int < 0 or y_int < 0 or x_int >= w - 1 or y_int >= h - 1:
        return (0, 0, 0)
    
    p1, p2 = pixels[y_int][x_int], pixels[y_int][x_int+1]
    p3, p4 = pixels[y_int+1][x_int], pixels[y_int+1][x_int+1]
    
    dx, dy = x - x_int, y - y_int
    res = []
    for i in range(3):
        top = p1[i] + dx * (p2[i] - p1[i])
        bottom = p3[i] + dx * (p4[i] - p3[i])
        res.append(int(top + dy * (bottom - top)))
    return tuple(res)

# --- ENCRYPTION (With Canvas Expansion) ---
def sender_encrypt(input_file, output_image, secret_twist):
    N, e = GenN()
    M = int(secret_twist * 10000)
    locked_message = LockM(M, e, N)
    
    pixels, w, h = readImage(input_file)
    
    # 1. Calculate Diagonal to prevent data loss
    diag = int(math.ceil(math.sqrt(w**2 + h**2)))
    new_w, new_h = diag, diag
    
    out_pixels = [[(0,0,0) for j in range(new_w)] for i in range(new_h)]
    
    # Centers
    cx_orig, cy_orig = w // 2, h // 2
    cx_new, cy_new = new_w // 2, new_h // 2
    
    for i in range(new_h):
        for j in range(new_w):
            dx, dy = j - cx_new, i - cy_new
            r = math.sqrt(dx**2 + dy**2)
            theta = math.atan2(dy, dx)
            
            # Reverse map to find where this pixel came from
            orig_theta = theta - (r * secret_twist)
            
            oc = cx_orig + r * math.cos(orig_theta)
            orow = cy_orig + r * math.sin(orig_theta)
            
            if 0 <= orow < h and 0 <= oc < w:
                out_pixels[i][j] = get_smooth_pixel(pixels, oc, orow, w, h)
                
    writeImage(out_pixels, output_image)
    return locked_message, e, w, h # We need original dimensions for decryption

# --- DECRYPTION ---
def receiver_decrypt(input_image, output_file, locked_msg, e_val, orig_w, orig_h):
    unlocked_m = UnlockM(locked_msg, e_val)
    recovered_twist = unlocked_m / 10000.0
    
    pixels, w_vault, h_vault = readImage(input_image)
    
    # Create output at ORIGINAL size
    out_pixels = [[(0,0,0) for j in range(orig_w)] for i in range(orig_h)]
    
    cx_vault, cy_vault = w_vault // 2, h_vault // 2
    cx_orig, cy_orig = orig_w // 2, orig_h // 2
    
    for i in range(orig_h):
        for j in range(orig_w):
            dx, dy = j - cx_orig, i - cy_orig
            r = math.sqrt(dx**2 + dy**2)
            theta = math.atan2(dy, dx)
            
            # Apply twist to find where it is in the vault
            vault_theta = theta + (r * recovered_twist)
            
            oc = cx_vault + r * math.cos(vault_theta)
            orow = cy_vault + r * math.sin(vault_theta)
            
            if 0 <= orow < h_vault and 0 <= oc < w_vault:
                out_pixels[i][j] = get_smooth_pixel(pixels, oc, orow, w_vault, h_vault)
                
    writeImage(out_pixels, output_file)

# --- EXECUTION ---
# Note: Keep twist moderate (e.g. 0.05) for best results
locked_message, e, orig_w, orig_h = sender_encrypt("image.png", "encrypted.jpg", 0.0954)
receiver_decrypt("encrypted.jpg", "decrypted.jpg", locked_message, e, orig_w, orig_h)