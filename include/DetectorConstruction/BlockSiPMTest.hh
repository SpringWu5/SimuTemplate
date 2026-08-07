#ifndef BLOCKSIPMTEST_HH
#define BLOCKSIPMTEST_HH

#include "DetectorConstruction/DetectorConstructionBase.hh"
#include "G4LogicalVolume.hh"

/**
 * @brief Small scintillator BLOCK for the block-vs-slab SiPM comparison.
 *
 * One EJ-200 block (default 2 x 3 x 3 cm) wrapped in reflective ESR, read out
 * by a SINGLE SiPM (default 6x6 mm active) placed at the centre of one 2x3 cm
 * side face. Only the active area is sensitive (records channel/time/wavelength,
 * no PDE). The scintillator also records Edep (VoxelTruth) for normalisation.
 *
 * Block axes (mm): X = edge-parallel (2 cm), Y = inward (3 cm),
 * Z = vertical, crossed by the muon (3 cm). The SiPM sits on the +Y face.
 *
 * Detector key: "blocktest".
 */
class BlockSiPMTest : public DetectorConstructionBase
{
public:
    explicit BlockSiPMTest(const char* config_path);
    virtual ~BlockSiPMTest() = default;

protected:
    virtual G4VPhysicalVolume* ConstructDetector(G4LogicalVolume* worldLogical) override;
    virtual void BuildSensitiveDetectors() override;

private:
    void LoadParameters();

    double fBx = 20.0, fBy = 30.0, fBz = 30.0;   // mm
    double fESRThick = 1.0;
    double fActiveThick = 0.5;
    double fESRReflectivity = 0.95;
    double fActiveSize = 6.0;                    // mm

    G4LogicalVolume* fLogicScint = nullptr;
    G4LogicalVolume* fLogicActive = nullptr;
};

#endif // BLOCKSIPMTEST_HH
