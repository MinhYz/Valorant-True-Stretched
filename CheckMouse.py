import ctypes

# Check tốc độ chuột hiện tại
speed = ctypes.c_int()
ctypes.windll.user32.SystemParametersInfoW(0x0070, 0, ctypes.byref(speed), 0)

# Check gia tốc chuột (0 là tắt)
accel = (ctypes.c_int * 3)()
ctypes.windll.user32.SystemParametersInfoW(0x0003, 0, ctypes.byref(accel), 0)

print(f"--- THÔNG SỐ HIỆN TẠI ---")
print(f"Tốc độ chuột (1-20): {speed.value}")
print(f"Gia tốc chuột (Enhance Pointer): {'ĐANG BẬT' if accel[2] != 0 else 'ĐÃ TẮT'}")