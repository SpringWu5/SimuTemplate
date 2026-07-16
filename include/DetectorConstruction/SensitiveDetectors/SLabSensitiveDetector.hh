/*
 * SLabSensitiveDetector.hh
 * 
 * Created on: 2024.09.28
 * Author: Weilun Huang
 */

#ifndef SLABSENSITIVEDETECTOR_HH
#define SLABSENSITIVEDETECTOR_HH

#include "G4VSensitiveDetector.hh"
#include "globals.hh"

class G4Material;
class G4HCofThisEvent;
class G4Step;

class SLabSensitiveDetector : public G4VSensitiveDetector
{
public:
    SLabSensitiveDetector(G4String);
    ~SLabSensitiveDetector();
    G4bool ProcessHits(G4Step *step, G4TouchableHistory *);

private:
    void DumpInfo(G4Step *step, G4TouchableHistory *touchable);
};

#endif