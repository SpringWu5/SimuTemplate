/*
 * SipmSensitiveDetector.hh
 * 
 * Created on: 2024.09.28
 * Author: Weilun Huang
 */

#ifndef SIPMSENSITIVEDETECTOR_HH
#define SIPMSENSITIVEDETECTOR_HH

#include "G4VSensitiveDetector.hh"
#include "globals.hh"
#include "Math/Interpolator.h"
#include "TRandom3.h"

class G4Material;
class G4HCofThisEvent;
class G4Step;

class SipmSensitiveDetector : public G4VSensitiveDetector
{
public:
    SipmSensitiveDetector(G4String name);
    ~SipmSensitiveDetector();
    G4bool ProcessHits(G4Step *step, G4TouchableHistory *);

private:
    void LoadSipmPhotonDetectionEfficiency();

    void DumpInfo(G4Step *step, G4TouchableHistory *touchable);
    ROOT::Math::Interpolator* fInterpPDE = nullptr;
    TRandom3* fRandomGen = 0;
};

#endif