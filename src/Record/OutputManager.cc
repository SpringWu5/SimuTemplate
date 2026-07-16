#include <G4SteppingVerbose.hh>
#include "Record/OutputManager.hh"
#include "TNamed.h"
#include <fstream>
#include <sstream>


OutputManager::OutputManager(): fOutputFile(0), fOutputTree(0),
    fPrimaryPDG(0), fPrimaryEnergy(0),
    fPrimaryX(0), fPrimaryY(0), fPrimaryZ(0),
    fPrimaryPx(0), fPrimaryPy(0), fPrimaryPz(0),
    fPrimaryTime(0)
{
    fMuons = new Muons();
    fSLabHits = new Hits();
    fHits = new Hits();
    fSiPMHits = new SiPMHit();
    fVoxelTruth = new VoxelTruthHit();
}

// Destructor: Ensure ROOT file is properly closed even if Save() wasn't called
OutputManager::~OutputManager()
{
    // Close the ROOT file if it is still open (i.e. Save() was not called).
    // TFile::Close() deletes every object it owns, including the TTree, so we
    // must NOT delete fOutputTree ourselves in any code path.
    if (fOutputFile) {
        G4cout << "OutputManager destructor: Closing ROOT file" << G4endl;
        fOutputFile->Write();
        fOutputFile->Close();   // deletes fOutputTree (owned by TFile)
        fOutputFile = nullptr;
        fOutputTree = nullptr;  // owned by the TFile -> never delete manually
    }

    // Hit-collection structs are NOT owned by the TFile; clean them up.
    delete fMuons;
    delete fSLabHits;
    delete fHits;
    delete fSiPMHits;
    delete fVoxelTruth;
}


void OutputManager::Book(G4String outfile, G4String configPath)
{
    // Creating a tree container to handle histograms and ntuples.
    // This tree is associated to an output file.
    //
    fOutputFileName = outfile;  // Store filename for geometry export
    fOutputFile = new TFile(outfile,"RECREATE");
    if(!fOutputFile) {
        G4cout << " OutputManager::book :"
               << " problem creating the ROOT TFile "
               << G4endl;
        return;
    }

    // Embed config file if provided
    if (configPath != "") {
        std::ifstream f(configPath);
        if (f.is_open()) {
            std::stringstream buffer;
            buffer << f.rdbuf();
            TNamed configName("ConfigFile", buffer.str().c_str());
            configName.Write();
            G4cout << "Config file embedded into ROOT file: " << configPath << G4endl;
        } else {
            G4cout << "Warning: Could not open config file " << configPath << " to save into ROOT." << G4endl;
        }
    }

    //info about event statistics
    fOutputTree = new TTree("Simu", "Simulation Tree");
    fOutputTree->Branch("eventID", &fEventID, "eventID/I");

    // Global Truth branches (Task 2)
    fOutputTree->Branch("Primary_PDG", &fPrimaryPDG, "Primary_PDG/I");
    fOutputTree->Branch("Primary_Energy", &fPrimaryEnergy, "Primary_Energy/D");
    fOutputTree->Branch("Primary_X", &fPrimaryX, "Primary_X/D");
    fOutputTree->Branch("Primary_Y", &fPrimaryY, "Primary_Y/D");
    fOutputTree->Branch("Primary_Z", &fPrimaryZ, "Primary_Z/D");
    fOutputTree->Branch("Primary_Px", &fPrimaryPx, "Primary_Px/D");
    fOutputTree->Branch("Primary_Py", &fPrimaryPy, "Primary_Py/D");
    fOutputTree->Branch("Primary_Pz", &fPrimaryPz, "Primary_Pz/D");
    fOutputTree->Branch("Primary_Time", &fPrimaryTime, "Primary_Time/D");

    // Muon branches
    fMuons->BookBranches(fOutputTree);

    // Voxel Truth branches (Task 3)
    fVoxelTruth->BookBranches(fOutputTree, "Voxel");

    // SiPM Hit branches (Task 1 - Slim)
    fSiPMHits->BookBranches(fOutputTree, "SiPM");

    // Legacy branches (kept for backward compatibility)
    fSLabHits->BookBranches(fOutputTree, "SLab");
    fHits->BookBranches(fOutputTree, "SiPM_Old");
}




void OutputManager::Save()
{
    if (fOutputFile) {
        G4cout << "OutputManager::Save(): Writing and closing ROOT file" << G4endl;
        fOutputFile->Write();       // Writing the histograms to the file
        fOutputFile->Close();        // and closing the tree (and the file)
        fOutputFile = nullptr;       // Mark as closed to prevent double-close in destructor
        fOutputTree = nullptr;       // ROOT deletes TTree when file closes, prevent double-free
        G4cout << "OutputManager::Save(): ROOT file closed successfully" << G4endl;
    }
}