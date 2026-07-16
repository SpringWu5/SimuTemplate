#ifndef SINGLESLABSIPMTEST_HH
#define SINGLESLABSIPMTEST_HH

#include "DetectorConstruction/DetectorConstructionBase.hh"
#include "G4LogicalVolume.hh"

/**
 * @brief Single-slab detector for the SiPM-sizing experiment.
 *
 * One EJ-200 scintillator slab (default 20x20x2 cm) read out by "unit SiPMs"
 * placed around its perimeter: 2 positions per edge at +/- position_offset,
 * i.e. 8 unit-SiPM sites total. A "unit SiPM" is one of three forms, selected
 * by SiPMTest.config:
 *   1 -> single 6x6 mm active area (physical 7x7)
 *   2 -> single 3x3 mm active area (physical 4x4)
 *   3 -> 2x2 array of 3x3 mm active areas (1 mm gap, 9x9 mm footprint)
 *
 * Only the active-area volumes are sensitive. The slab (bar the SiPM windows)
 * is wrapped in a reflective ESR shell. Channel ID encoding:
 *   edge(0..3)*1000 + pos(0..1)*100 + cell(0..3)
 * where edge: 0=+X,1=-X,2=+Y,3=-Y and cell is the array sub-channel (0 for the
 * single-SiPM configs).
 */
class SingleSlabSiPMTest : public DetectorConstructionBase
{
public:
    explicit SingleSlabSiPMTest(const char* config_path);
    virtual ~SingleSlabSiPMTest() = default;

protected:
    virtual G4VPhysicalVolume* ConstructDetector(G4LogicalVolume* worldLogical) override;
    virtual void BuildSensitiveDetectors() override;

private:
    void LoadParameters();

    // Geometry (mm), read from the SiPMTest YAML node
    double fSlabX = 200.0, fSlabY = 200.0, fSlabZ = 20.0;
    double fESRThick = 1.0;
    double fActiveThick = 0.5;
    double fESRReflectivity = 0.95;
    double fPosOffset = 50.0;  // SiPM position along each edge (+/-)

    // SiPM "unit" geometry derived from fConfig
    int    fConfig = 1;        // 1, 2 or 3
    double fActiveSize = 6.0;  // active-area side (mm): 6 for C1, 3 for C2/C3
    int    fArrayN = 1;        // 1 (single) or 2 (2x2 array)
    double fCellPitch = 0.0;   // centre-to-centre pitch (mm) for arrays

    G4LogicalVolume* fLogicScint = nullptr;
    G4LogicalVolume* fLogicActiveX = nullptr;  // active areas on +/-X faces
    G4LogicalVolume* fLogicActiveY = nullptr;  // active areas on +/-Y faces
};

#endif // SINGLESLABSIPMTEST_HH
