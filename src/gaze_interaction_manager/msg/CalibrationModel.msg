# Model Type Enums
uint8 TYPE_BIAS=0
uint8 TYPE_QUADRATIC=1
uint8 TYPE_RADIAL_UNIVERSAL=2
uint8 TYPE_SIGMOIDAL=3
uint8 TYPE_KNN_GRID=4
uint8 TYPE_LINEAR=5

uint8 model_type

# 0-5 Polynomial [x^2, y^2, xy, x, y, 1]
# 6-7 Sigmoidal [amplitude, scale]
# 8 Radial k
float64[] coeffs_x  
float64[] coeffs_y
# For KNN grid fallback
float32[] grid_vectors_x
float32[] grid_vectors_y
uint32 grid_cols
uint32 grid_rows