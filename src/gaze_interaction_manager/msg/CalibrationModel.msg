uint8 TYPE_QUADRATIC=0
uint8 TYPE_KNN_GRID=1

uint8 model_type
float64[] coeffs_x   # [x^2, y^2, xy, x, y, 1]
float64[] coeffs_y
# For KNN grid fallback
float32[] grid_vectors_x
float32[] grid_vectors_y
uint32 grid_cols
uint32 grid_rows