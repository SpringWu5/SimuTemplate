/*
 * MaterialManager.hh
 * 
 * Created on: 2024.09.28
 * Author: Weilun Huang
 */

#ifndef MATERIALMANAGER_HH
#define MATERIALMANAGER_HH

#include "G4Element.hh"
#include "G4Material.hh"
#include "G4SystemOfUnits.hh"
#include "Util/Logger.hh"
#include "Util/Singleton.hh"
#include "yaml-cpp/yaml.h"
#include "map"
#include "string"

struct SLabGeometry
{
    double Scintxlength;
    double Scintylength;
    double Scintzlength;
    double ESRthickness;
    double Tapethickness;
    double SiPMxlength;
    double SiPMylength;
    double SiPMzlength;
    double Batteryxlength;
    double Batteryylength;
    double Batteryzlength;
    std::vector<double> slabOffsets;
    int numberOfSlabs;
};

struct OpticalProperty
{
    int num;
    std::vector<double> energy;
    std::vector<double> refracIdxPhase;
    std::vector<double> refracIdxGroup;
    std::vector<double> absLen;
    std::vector<double> scaLenRay;
    std::vector<double> scaLenMie;
    double mieForward;
};


struct SipmProperty
{
    G4int Num = 5;
    G4double Ephoton[5] = {
        2.06667 * eV,
        2.5 * eV,
        3.0 * eV,
        3.5 * eV,
        4.13333 * eV};
    G4double Reflection[5] = {
        0.1,
        0.1,
        0.1,
        0.1,
        0.1};
    G4double RelativeEfficiency[5] = {
        1.0,
        1.0,
        1.0,
        1.0,
        1.0};
    G4double MaxEfficiency = 0.6;
};


class MaterialManager : public Singleton<MaterialManager> {
public:
    YAML::Node getRootNode() { return rootNode; }

    bool BuildEverything(const G4String &fileYAML);

    G4Material *GetMaterial(std::string name);
    float *GetArrayProperites();
    SLabGeometry GetSLabGeometry() { return fSLabGeometry; }
    SipmProperty GetSipmProperty() { return fSipmProperty; }

private:
    friend class Singleton<MaterialManager>;
    MaterialManager() {};
    void LoadYAML();
    void BuildElement();
    void BuildMaterial();

    void BuildOpticalProperties();

    // medium of sea
    void BuildSeaWater();

    void BuildIce();

    // material for DOM protection glass and PMT glass,
    // not precise, it also contains B2O3、Na2O
    void BuildGlass();

    // material for support in DOM, not precise
    void BuildEpoxy();

    // not precise
    void BuildGel();

    // not precise
    void BuildSiPM();

    void BuildScint();

    void BuildESR();

    void BuildTape();

    void BuildBattery();

    /**
     * @brief Build SP101 plastic scintillator material for MuonCube
     *
     * SP101 is a polystyrene-based scintillator with custom optical properties.
     * Spectrum is loaded from external file specified in config.
     */
    void BuildSP101();

    /**
     * @brief Build BCF-92 WLS Fiber Core material
     *
     * Polystyrene-based WLS fiber with absorption and emission properties.
     */
    void BuildBCF92_Core();

    /**
     * @brief Build BCF-92 WLS Fiber Cladding material
     *
     * PMMA-based cladding with high transparency.
     */
    void BuildBCF92_Clad();

    /**
     * @brief Build G4_AIR with optical properties (CRITICAL FIX)
     *
     * Geant4 kills optical photons at boundaries to materials without RINDEX.
     * This method adds RINDEX=1.0 to G4_AIR to enable optical photon propagation.
     * MUST be called before any geometry construction.
     */
    void BuildAirWithOptics();

    G4MaterialPropertiesTable* SetOpticalPropertiesOfPS();

    /**
     * @brief Load scintillation spectrum from external file
     *
     * Reads a two-column file (wavelength [nm], intensity) and converts
     * to GEANT4 format (energy [eV], intensity).
     *
     * @param filename Path to spectrum file
     * @param energies Output vector of photon energies
     * @param intensities Output vector of scintillation intensities
     * @return true if successful, false otherwise
     */
    bool LoadSpectrum(const std::string& filename,
                      std::vector<G4double>& energies,
                      std::vector<G4double>& intensities);

    std::shared_ptr<spdlog::logger> logger;
    G4Element *fElH, *fElC, *fElO, *fElNa, *fElSi, *fElCl;
    G4MaterialPropertiesTable *fMediumOpticalProperties;
    std::map<std::string, G4Material *> fMapMaterial;

    YAML::Node rootNode;
    SLabGeometry fSLabGeometry;
    OpticalProperty fSeaOpticalProperty;
    SipmProperty fSipmProperty;
};

#endif