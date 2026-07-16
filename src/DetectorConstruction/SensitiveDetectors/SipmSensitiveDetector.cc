#include "DetectorConstruction/SensitiveDetectors/SipmSensitiveDetector.hh"
#include "DetectorConstruction/MaterialManager.hh"
#include "Record/Hits.hh"
#include "Record/OutputManager.hh"

#include "G4Material.hh"
#include "G4Step.hh"
#include "G4VTouchable.hh"
#include "G4TouchableHistory.hh"
#include "G4SDManager.hh"
#include "G4OpticalPhoton.hh"
#include "G4ParticleDefinition.hh"
#include "G4MuonPlus.hh"
#include "G4MuonMinus.hh"
#include "Randomize.hh"
#include "G4SystemOfUnits.hh"
#include "g4root.hh"
#include "spdlog/spdlog.h"

#include <stdexcept>

using std::vector;
using std::string;
SipmSensitiveDetector::SipmSensitiveDetector(G4String name) : G4VSensitiveDetector(name)
{
    LoadSipmPhotonDetectionEfficiency();
    fRandomGen = new TRandom3(0);
}

SipmSensitiveDetector::~SipmSensitiveDetector()
{
}

void SipmSensitiveDetector::LoadSipmPhotonDetectionEfficiency()
{
    vector<double> wave_length, detection_efficiency;
    
    std::ifstream sipm_pde_file;
    auto config_node = MaterialManager::Instance()->getRootNode();
    string pde_path = config_node["Property"]["sipm"]["pde_file"].as<string>();
    sipm_pde_file.open(pde_path);
    if (!sipm_pde_file.is_open())
    {
        spdlog::error("Failed to open SiPM PDE file: {:s}", pde_path);
        throw std::runtime_error("SipmSensitiveDetector: failed to open SiPM PDE file: " + pde_path);
    } else {
        spdlog::info("SiPM PDE file opened: {:s}", pde_path);
        double wl, eff;
        while (sipm_pde_file >> wl >> eff)
        {
            wave_length.push_back(wl);
            detection_efficiency.push_back(eff/100.);
        }
    }
    fInterpPDE = new ROOT::Math::Interpolator(wave_length, detection_efficiency, ROOT::Math::Interpolation::kLINEAR);
}

G4bool SipmSensitiveDetector::ProcessHits(G4Step *step, G4TouchableHistory *)
{
    spdlog::debug("SiPM HIT: pre-step volume: {:s}, post-step volume: {:s}",
                    step->GetPreStepPoint()->GetPhysicalVolume()->GetName(),
                    step->GetPostStepPoint()->GetPhysicalVolume()->GetName());

    Hits* hits = OutputManager::Instance()->GetHits();
    HitType hitType = HitType::Others;
    if (step->GetTrack()->GetDefinition() == G4OpticalPhoton::Definition())
    {
        // check if the optical photon is detected by SiPM
        double wl = 1240. / (step->GetPostStepPoint()->GetKineticEnergy() / eV);
        G4double detection_efficiency = fInterpPDE->Eval(wl);
        if (fRandomGen->Uniform() > detection_efficiency)
        {
            // TODO: seems donot need to kill the track. May need to double check
            return true;
        }
        hitType = HitType::OpticalPhoton;
        step->GetTrack()->SetTrackStatus(fStopAndKill);
    } else if (step->GetTrack()->GetDefinition() == G4MuonMinus::Definition() ||
        step->GetTrack()->GetDefinition() == G4MuonPlus::Definition())
    {
        hitType = HitType::Muon;
    }

    G4int trackID = step->GetTrack()->GetTrackID();
    G4StepPoint* postStepPoint = step->GetPostStepPoint();

    // CRITICAL FIX: Energy semantics differ by particle type
    Float_t energy = 0.;
    if (hitType == HitType::OpticalPhoton) {
        // For optical photons: record photon energy (for wavelength/PDE)
        energy = postStepPoint->GetKineticEnergy();
    } else {
        // For charged particles (muons, etc.): record energy deposit
        energy = step->GetTotalEnergyDeposit();
        // Filter out zero-deposit hits
        if (energy == 0.) return false;
    }

    G4ThreeVector momentum = postStepPoint->GetMomentum();
    G4ThreeVector pos = postStepPoint->GetPosition();
    Float_t hitTime = postStepPoint->GetGlobalTime() / ns;
    auto touchable =
        static_cast<const G4TouchableHistory *>(step->GetPreStepPoint()->GetTouchable());
    int SiPMID = touchable->GetCopyNumber(0);

    // Energy unit: GeV for photons (eV range), MeV for energy deposit
    Float_t energy_unit = (hitType == HitType::OpticalPhoton) ? GeV : MeV;
    Float_t stepLen = step->GetStepLength() / cm;
    hits->AddHit(
        hitType, trackID, SiPMID,
        energy/energy_unit, momentum.x()/GeV, momentum.y()/GeV, momentum.z()/GeV,
        pos.x()/cm, pos.y()/cm, pos.z()/cm, hitTime,
        stepLen
    );

    return true;
}

void SipmSensitiveDetector::DumpInfo(G4Step *step, G4TouchableHistory *touchable)
{
    // code for understanding the return value of Geant4 function
    G4cout << "*******************************" << G4endl;
    G4cout << "             SiPM HIT           " << G4endl;
    G4cout << "  touchable->GetCopyNumber(0): "
            << touchable->GetCopyNumber(0) << G4endl;
    G4cout << "  touchable->GetCopyNumber(2): "
            << touchable->GetCopyNumber(2) << G4endl;
    G4cout << "  touchable->GetVolume(2)->GetTranslation(): "
            << touchable->GetVolume(2)->GetTranslation().x() / CLHEP::mm << " "
            << touchable->GetVolume(2)->GetTranslation().y() / CLHEP::mm << " "
            << touchable->GetVolume(2)->GetTranslation().z() / CLHEP::mm << G4endl;
    G4cout << "  step->GetTrack()->GetKineticEnergy() (eV) : "
            << step->GetTrack()->GetKineticEnergy() / CLHEP::eV << G4endl;
    G4ThreeVector VecSipmToPhoton = step->GetPostStepPoint()->GetPosition() - touchable->GetVolume(2)->GetTranslation();
    G4cout << "  VecSipmToPhoton (mm) : "
            << VecSipmToPhoton.x() / CLHEP::mm << " "
            << VecSipmToPhoton.y() / CLHEP::mm << " "
            << VecSipmToPhoton.z() / CLHEP::mm << G4endl;
    G4cout << "  step->GetPostStepPoint()->GetMomentumDirection(): "
            << step->GetPostStepPoint()->GetMomentumDirection().x() << " "
            << step->GetPostStepPoint()->GetMomentumDirection().y() << " "
            << step->GetPostStepPoint()->GetMomentumDirection().z() << G4endl;
    G4cout << "  step->GetPostStepPoint()->GetGlobalTime() (ns): "
            << step->GetPostStepPoint()->GetGlobalTime() / CLHEP::ns << G4endl;
    G4cout << "*******************************" << G4endl << G4endl;
}