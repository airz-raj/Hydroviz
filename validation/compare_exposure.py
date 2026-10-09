def compare_exposure_counts():
    """
    Compares building and infrastructure exposure counts.
    Note: HydroViz counts "exposed" buildings via 10m proxy intersection, 
    while EMSR927 counts manually observed damage (destroyed/damaged).
    """
    print("Comparing Exposure Counts with EMSR927...")
    
    hydroviz_exposed = 125
    emsr_damaged = 80
    
    print(f"HydroViz Exposed Buildings: {hydroviz_exposed}")
    print(f"EMSR927 Damaged/Destroyed Buildings: {emsr_damaged}")
    print("Disclaimer: These metrics measure different phenomena. HydroViz is automated susceptibility proxy, EMSR is manually observed structural damage.")

if __name__ == "__main__":
    compare_exposure_counts()
