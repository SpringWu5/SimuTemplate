/*
 * OutputManager.hh
 *
 * ML-Optimized Output Manager (Phase 3.0)
 *
 * Created on: 2024.09.29
 * Author: Cen Mo
 * Modified: 2025 (Claude Code) - ML Refactoring
 */

#ifndef OUTPUTMANAGER_HH
#define OUTPUTMANAGER_HH

#include "TFile.h"
#include "TTree.h"
#include "G4String.hh"

#include "Record/Muons.hh"
#include "Record/Hits.hh"
#include "Record/SiPMHit.hh"
#include "Record/VoxelTruthHit.hh"
#include "Util/Singleton.hh"

class OutputManager : public Singleton<OutputManager>
{
public:
    void Book(G4String outfile, G4String configPath = "");
    void Fill() { fOutputTree->Fill(); }
    void Save();
    ~OutputManager();  // Destructor: Ensures ROOT file is properly closed

    void EndOfEvent() {
        Fill();
        fMuons->Reset();
        fSLabHits->Reset();
        fHits->Reset();
        fSiPMHits->Reset();
        fVoxelTruth->Reset();
    }

    void SetEventID(Int_t eID) { fEventID = eID; }

    Int_t GetEventID() { return fEventID; }
    G4String GetOutputFileName() { return fOutputFileName; }

    Muons* GetMuons() { return fMuons; }
    Hits* GetSLabHits() { return fSLabHits; }
    Hits* GetHits() { return fHits; }
    SiPMHit* GetSiPMHits() { return fSiPMHits; }
    VoxelTruthHit* GetVoxelTruth() { return fVoxelTruth; }

    // Global Truth setters
    void SetPrimaryPDG(int pdg) { fPrimaryPDG = pdg; }
    void SetPrimaryEnergy(double e) { fPrimaryEnergy = e; }
    void SetPrimaryPosition(double x, double y, double z) {
        fPrimaryX = x; fPrimaryY = y; fPrimaryZ = z;
    }
    void SetPrimaryMomentum(double px, double py, double pz) {
        fPrimaryPx = px; fPrimaryPy = py; fPrimaryPz = pz;
    }
    void SetPrimaryTime(double t) { fPrimaryTime = t; }

private:
    friend class Singleton<OutputManager>;
    OutputManager();

    TFile*   fOutputFile;
    TTree*   fOutputTree;
    G4String fOutputFileName;  // Store output filename for geometry export

    Int_t    fEventID;

    // Hit collections
    Muons*   fMuons;
    Hits*    fSLabHits;      // Legacy (kept for backward compatibility)
    Hits*    fHits;          // Legacy (kept for backward compatibility)
    SiPMHit* fSiPMHits;      // NEW: Slim SiPM hits
    VoxelTruthHit* fVoxelTruth;  // NEW: Voxel-level truth

    // Global Truth (scalars)
    Int_t    fPrimaryPDG;
    Double_t fPrimaryEnergy;
    Double_t fPrimaryX, fPrimaryY, fPrimaryZ;
    Double_t fPrimaryPx, fPrimaryPy, fPrimaryPz;
    Double_t fPrimaryTime;
};


#endif