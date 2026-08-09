#ifndef STACKEDDETECTOR_HH
#define STACKEDDETECTOR_HH

#include "DetectorConstruction/DetectorConstructionBase.hh"
#include "G4LogicalVolume.hh"

class G4OpticalSurface;

/**
 * @brief Full stacked detector for the phase-3 optical study.
 *
 *   upper small scints (Ch0 right, Ch1 left)  at z = +L/2
 *   ---------------- central slab 20x20x2 cm ----------------  z in [-1,1]
 *   lower small scints (Ch2 right, Ch3 left)  at z = -L/2
 *
 * Slab read out by 8 SiPMs (Ch4..Ch11) on its 4 edges (2 per edge at +/-5 cm),
 * each 6x6 mm active, recorded as slim photon hits (channel/time/wavelength).
 * Small scints are ESR-wrapped scintillators; their Edep is recorded (trigger
 * proxy) but their individual SiPM readout is NOT modelled (not specified).
 *
 * ESR optical surface is parametrised (reflectivity, sigma_alpha roughness,
 * finish) so O2/O3/O4 surface scans are pure config changes.
 *
 * Detector key: "stacked".
 *
 * Slab SiPM channel map (edge*1000 + pos*100):
 *   edge0=+x : 0(+5cm y)=Ch4, 100(-5cm)=Ch5
 *   edge1=-x : 1000=Ch8, 1100=Ch9
 *   edge2=+y : 2000=Ch6, 2100=Ch7
 *   edge3=-y : 3000=Ch11(+5cm x), 3100=Ch10(-5cm x)
 * (Ch11 near +x Ch0/Ch2 path; Ch10 near -x Ch1/Ch3 path.)
 */
class StackedDetector : public DetectorConstructionBase
{
public:
    explicit StackedDetector(const char* config_path);
    virtual ~StackedDetector() = default;

protected:
    virtual G4VPhysicalVolume* ConstructDetector(G4LogicalVolume* worldLogical) override;
    virtual void BuildSensitiveDetectors() override;

private:
    void LoadParameters();
    G4OpticalSurface* MakeESRSurface(const G4String& name);

    // geometry (cm unless noted)
    double fLsep = 10.0, fGap = 10.0;
    double fSlabHx = 10.0, fSlabHy = 10.0, fSlabHz = 1.0;
    double fBlkHx = 1.0, fBlkHy = 1.5, fBlkHz = 1.5;
    double fSipmActive = 6.0;   // mm
    double fESRThick = 0.1;     // cm
    // optical params (scanned)
    double fRefl = 0.95;
    double fSigmaAlphaDeg = 0.0;
    G4String fFinish = "groundfrontpainted";   // ESR finish: groundfrontpainted(diffuse) | polished(specular) | ground

    G4LogicalVolume* fLogicSlab = nullptr;
    G4LogicalVolume* fLogicSmall[4] = {nullptr, nullptr, nullptr, nullptr};
    G4LogicalVolume* fLogicActiveX = nullptr;
    G4LogicalVolume* fLogicActiveY = nullptr;
};

#endif // STACKEDDETECTOR_HH
