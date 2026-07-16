#include "PhysicsList/PhysicsList.hh"
#include "PhysicsList/MilliQEMPhysics.hh"
#include "PhysicsList/MilliQMuonPhysics.hh"

#include <iomanip>
#include "globals.hh"
#include "G4ios.hh"
#include "G4ProcessManager.hh"
#include "G4ProcessVector.hh"
#include "G4ParticleTypes.hh"
#include "G4ParticleTable.hh"

#include "G4Material.hh"
#include "G4MaterialTable.hh"
#include "G4PhysicalConstants.hh"
#include "G4SystemOfUnits.hh"
#include "G4NistManager.hh"

#include "G4DecayPhysics.hh"
#include "G4RadioactiveDecayPhysics.hh"
#include "G4EmProcessOptions.hh"
#include "G4EmStandardPhysics_option4.hh"
#include "G4EmExtraPhysics.hh"
#include "G4IonQMDPhysics.hh"
#include "G4IonElasticPhysics.hh"
#include "G4StoppingPhysics.hh"
#include "G4HadronElasticPhysicsHP.hh"
#include "G4HadronElasticPhysicsLEND.hh"
#include "G4EmCalculator.hh"
#include "G4ParticleDefinition.hh"
#include "G4MuonMinus.hh"
#include "G4MuonPlus.hh"
#include "G4Material.hh"

#include "G4HadronPhysicsShielding.hh"

#include "G4OpticalPhysics.hh"

#include <cstdlib>   // setenv

PhysicsList::PhysicsList(G4int verbose)
{
    G4cout << "<<< Geant4 Physics List simulation engine: Shielding 2.1"<<G4endl;
    G4cout <<G4endl;
    this->defaultCutValue = 0.7*CLHEP::mm; //used 0.01mm in smallStep run
    this->SetVerboseLevel(verbose);

    // EM Physics - CRITICAL FIX: Only register ONCE to avoid process duplication
    // MilliQEMPhysics and MilliQMuonPhysics provide custom EM and muon processes
    // RegisterPhysics( new MilliQEMPhysics("standard EM"));

    // Muon Physics
    // RegisterPhysics( new MilliQMuonPhysics("muon"));

    // EM Physics - High Precision Option 4
    this->RegisterPhysics( new G4EmStandardPhysics_option4(verbose));

    // Synchroton Radiation & GN Physics
    this->RegisterPhysics( new G4EmExtraPhysics(verbose) );

    // Decays
    this->RegisterPhysics( new G4DecayPhysics(verbose) );
    this->RegisterPhysics( new G4RadioactiveDecayPhysics(verbose) );

    // Hadron Elastic scattering
    this->RegisterPhysics( new G4HadronElasticPhysicsHP(verbose) );

    // Hadron Physics
    G4HadronPhysicsShielding* hps = new G4HadronPhysicsShielding(verbose);

    this->RegisterPhysics( hps );

    //Activate prodcuton of fission fragments in neutronHP
    // Use setenv() (copies its argument) instead of putenv() with a stack
    // buffer: putenv() keeps the pointer, so a local array would dangle.
    setenv("G4NEUTRONHP_PRODUCE_FISSION_FRAGMENTS", "1", 1);

    // Stopping Physics
    this->RegisterPhysics( new G4StoppingPhysics(verbose) );

    // Ion Physics
    this->RegisterPhysics( new G4IonQMDPhysics(verbose));

    this->RegisterPhysics( new G4IonElasticPhysics(verbose));

    // Neutron tracking cut --> not by default
    // this->RegisterPhysics( new G4NeutronTrackingCut(verbose));

    // ============================================================
    // Phase 2.3: Enable Optical Physics for MuonCube
    // ============================================================
    G4OpticalPhysics* opticalPhysics = new G4OpticalPhysics();

    opticalPhysics->SetScintillationYieldFactor(1.0);  // CRITICAL: Ensure yield is not zero
    opticalPhysics->SetTrackSecondariesFirst(kCerenkov, true);
    opticalPhysics->SetTrackSecondariesFirst(kScintillation, true);
    opticalPhysics->SetMaxNumPhotonsPerStep(100);

    this->RegisterPhysics( opticalPhysics );

    G4cout << "=== Optical Physics ENABLED (Phase 2.3) ===" << G4endl;
    G4cout << "  - Scintillation: ON (Yield Factor: 1.0)" << G4endl;
    G4cout << "  - WLS (Wavelength Shifting): ON" << G4endl;
    G4cout << "  - Cerenkov: ON" << G4endl;
    // ============================================================

    // NOTE: a dE/dx self-test using G4EmCalculator used to live here. It
    // constructed a throwaway "plScintillator" material (leaked) and printed
    // dE/dx before the physics tables were built (always 0, hence misleading).
    // Removed -- the real dE/dx comes from the registered EM physics at run time.
}

PhysicsList::~PhysicsList()
{
}

void PhysicsList::SetCuts()
{
    if (this->verboseLevel >1){
        G4cout << "Shielding::SetCuts:";
    }
    //  " G4VUserPhysicsList::SetCutsWithDefault" method sets
    //   the default cut value for all particle types
    this->SetCutValue(0.05*CLHEP::mm, "gamma");
    this->SetCutValue(0.05*CLHEP::mm, "e-");
    this->SetCutValue(0.05*CLHEP::mm, "e+");
    this->SetCutValue(0.05*CLHEP::mm, "proton");
    
    this->SetCutsWithDefault();
}




