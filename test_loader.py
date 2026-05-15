"""Quick test for the data loader."""
import sys
sys.path.insert(0, '.')

# Mock streamlit cache_data decorator
import streamlit
streamlit.cache_data = lambda *a, **kw: (lambda f: f)

from data_loader import (
    load_bookings_actuals,
    load_forecast_targets,
    load_forecast_accuracy,
    load_scms,
    load_vms,
    load_big_deals,
    load_product_metadata,
)

print("=== BOOKINGS ===")
b = load_bookings_actuals()
print(f"Shape: {b.shape}")
print(b[["Product", "FY23 Q2", "FY26 Q1"]].head())
print()

print("=== FORECAST TARGETS ===")
ft = load_forecast_targets()
print(f"Shape: {ft.shape}")
print(ft.head())
print()

print("=== FORECAST ACCURACY ===")
fa = load_forecast_accuracy()
print(f"Shape: {fa.shape}")
print(fa.head(9))
print()

print("=== SCMS ===")
s = load_scms()
print(f"Shape: {s.shape}")
prods = s["Product"].nunique()
segs = s["Segment"].nunique()
print(f"Products: {prods}, Segments: {segs}")
print(s.head())
print()

print("=== VMS ===")
v = load_vms()
print(f"Shape: {v.shape}")
vp = v["Product"].nunique()
vv = v["Vertical"].nunique()
print(f"Products: {vp}, Verticals: {vv}")
print()

print("=== BIG DEALS ===")
bd = load_big_deals()
print(f"Shape: {bd.shape}")
bdp = bd["Product"].nunique()
print(f"Products: {bdp}")
print(bd.head())
print()

print("=== METADATA ===")
m = load_product_metadata()
print(f"Shape: {m.shape}")
print(m[["Product", "Lifecycle"]].head())
print("Lifecycle distribution:")
print(m["Lifecycle"].value_counts())
print()

print("ALL TESTS PASSED!")
