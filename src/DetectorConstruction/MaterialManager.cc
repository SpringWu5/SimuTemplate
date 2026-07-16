#include "DetectorConstruction/MaterialManager.hh"
#include "G4Molecule.hh"
#include "G4SystemOfUnits.hh"
#include "G4MaterialTable.hh"
#include "G4NistManager.hh"
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>
#include <iterator>
#include <fstream>
#include <stdexcept>

using std::string;
using std::vector;

bool MaterialManager::BuildEverything(const G4String &fileYAML)
{
    logger = create_logger("MaterialManager");
    rootNode = YAML::LoadFile(fileYAML);
    try {
        LoadYAML();
    }
    catch (YAML::BadConversion &e)
    {
        logger->error("[Read YAML] ==> {:s}", e.msg);
        return false;
    }
    catch (YAML::InvalidNode &e)
    {
        logger->error("[Read YAML] ==> {:s}", e.msg);
        return false;
    }

    BuildElement();
    BuildOpticalProperties();
    BuildMaterial();
    return true;
}

void MaterialManager::LoadYAML()
{
    // Load SLab geometry
    auto node = rootNode["Geometry"]["SLab"];
    fSLabGeometry.Scintxlength = node["Scintillator"]["x_length"].as<double>() * cm;
    fSLabGeometry.Scintylength = node["Scintillator"]["y_length"].as<double>() * cm;
    fSLabGeometry.Scintzlength = node["Scintillator"]["z_length"].as<double>() * cm;
    fSLabGeometry.ESRthickness = node["ESR"]["thickness"].as<double>() * cm;
    fSLabGeometry.Tapethickness = node["Tape"]["thickness"].as<double>() * cm;
    fSLabGeometry.SiPMxlength = node["SiPM"]["x_length"].as<double>() * cm;
    fSLabGeometry.SiPMylength = node["SiPM"]["y_length"].as<double>() * cm;
    fSLabGeometry.SiPMzlength = node["SiPM"]["z_length"].as<double>() * cm;
    fSLabGeometry.Batteryxlength = node["Battery"]["x_length"].as<double>() * cm;
    fSLabGeometry.Batteryylength = node["Battery"]["y_length"].as<double>() * cm;
    fSLabGeometry.Batteryzlength = node["Battery"]["z_length"].as<double>() * cm;

    fSLabGeometry.numberOfSlabs = node["Layout"]["number_of_slabs"].as<int>();
    fSLabGeometry.slabOffsets = node["Layout"]["slab_offsets"].as<std::vector<double>>();

    // Load sea optical properties
    string pathFile = rootNode["Property"]["sea_optical_property"]["path_file"].as<string>();
    logger->debug("Reading config YAML file: optical properties");
    node = YAML::LoadFile(pathFile);
    fSeaOpticalProperty.energy = node["energy"].as<vector<double>>();
    fSeaOpticalProperty.num = fSeaOpticalProperty.energy.size();
    fSeaOpticalProperty.refracIdxPhase = node["refractive_index_phase"].as<vector<double>>();
    fSeaOpticalProperty.refracIdxGroup = node["refractive_index_group"].as<vector<double>>();
    fSeaOpticalProperty.absLen = node["absorption_length"].as<vector<double>>();
    fSeaOpticalProperty.scaLenRay = node["scatter_length_rayeigh"].as<vector<double>>();
    fSeaOpticalProperty.scaLenMie = node["scatter_length_mie"].as<vector<double>>();
    fSeaOpticalProperty.mieForward = node["mie_forward_angle"].as<double>();
    // set unit
    for (auto &eng : fSeaOpticalProperty.energy) { eng *= eV; }
    for (auto &len : fSeaOpticalProperty.absLen) { len *=  m; }
    for (auto &len : fSeaOpticalProperty.scaLenRay) { len *= m; }
    for (auto &len : fSeaOpticalProperty.scaLenMie) { len *= m; }
    for (auto& offset : fSLabGeometry.slabOffsets) {
        offset *= cm;
    }
}

void MaterialManager::BuildElement()
{
    // define element
    G4double a; // Zeff
    a = 1.01 * g / mole;
    fElH = new G4Element("Hydrogen", "H", 1., a);
    a = 12.01 * g / mole;
    fElC = new G4Element("Carbon", "C", 6., a);
    a = 16.00 * g / mole;
    fElO = new G4Element("Oxygen", "O", 8., a);
    a = 28.00 * g / mole;
    fElSi = new G4Element("Silicon", "Si", 14., a);
    a = 22.99 * g / mole;
    fElNa = new G4Element("Sodium", "Na", 11, a);
    a = 35.453 * g / mole;
    fElCl = new G4Element("Chlorine", "Cl", 17., a);
    logger->info("Finish building element");
}

void MaterialManager::BuildMaterial()
{
    // CRITICAL FIX: Build Air with optical properties FIRST
    // This must be done before any geometry that uses G4_AIR
    BuildAirWithOptics();

    // build vacuum
    G4Material *Vacuum = new G4Material("Vacuum", 1., 1.01 * g / mole, 1.e-25 * g / cm3, kStateGas, 2.73 * kelvin, 3.e-18 * pascal);
    fMapMaterial.insert({"Vacuum", Vacuum});

    BuildSeaWater();
    BuildGlass();
    BuildEpoxy();
    BuildGel();
    BuildSiPM();
    BuildScint();
    BuildESR();
    BuildTape();
    BuildBattery();
    BuildSP101();      // Add SP101 for MuonCube
    BuildBCF92_Core(); // Add BCF-92 WLS Fiber Core (Phase 2.0)
    BuildBCF92_Clad(); // Add BCF-92 WLS Fiber Cladding (Phase 2.0)
    logger->info("Finish building material");
}

G4Material *MaterialManager::GetMaterial(std::string name)
{
    auto iter = fMapMaterial.find(name);
    if (iter != fMapMaterial.end())
    {
        return iter->second;
    }
    else
    {
        logger->error("No material named {:s} has been found!", name);
        throw std::runtime_error("MaterialManager: no material named '" + name + "' has been found");
    }
}

void MaterialManager::BuildOpticalProperties()
{
    fMediumOpticalProperties = new G4MaterialPropertiesTable();
    fMediumOpticalProperties->AddProperty("RINDEX", fSeaOpticalProperty.energy.data(), fSeaOpticalProperty.refracIdxPhase.data(), fSeaOpticalProperty.num)->SetSpline(false);
    fMediumOpticalProperties->AddProperty("ABSLENGTH", fSeaOpticalProperty.energy.data(), fSeaOpticalProperty.absLen.data(), fSeaOpticalProperty.num)->SetSpline(false);
    fMediumOpticalProperties->AddProperty("RAYLEIGH", fSeaOpticalProperty.energy.data(), fSeaOpticalProperty.scaLenRay.data(), fSeaOpticalProperty.num)->SetSpline(false);
    if (fSeaOpticalProperty.mieForward)
    {
        fMediumOpticalProperties->AddProperty("MIEHG", fSeaOpticalProperty.energy.data(), fSeaOpticalProperty.scaLenMie.data(), fSeaOpticalProperty.num)->SetSpline(false);
        fMediumOpticalProperties->AddConstProperty("MIEHG_FORWARD", fSeaOpticalProperty.mieForward);
        fMediumOpticalProperties->AddConstProperty("MIEHG_BACKWARD", 0.0);
        fMediumOpticalProperties->AddConstProperty("MIEHG_FORWARD_RATIO", 1.0);
    }
}

void MaterialManager::BuildSeaWater()
{
    // build material component
    G4Material *H2O = new G4Material("Water", 1.00 * g / cm3, 2);
    H2O->AddElement(fElH, 2);
    H2O->AddElement(fElO, 1);
    G4Material *NaCl = new G4Material("Sodium Chlorure", 2.16 * g / cm3, 2);
    NaCl->AddElement(fElNa, 1);
    NaCl->AddElement(fElCl, 1);
    G4Material *SeaWater = new G4Material("Sea Water", 1.04 * g / cm3, 2, kStateLiquid,
                                            300. * atmosphere, 275. * kelvin);
    SeaWater->AddMaterial(NaCl, 3.5 * perCent);
    SeaWater->AddMaterial(H2O, 96.5 * perCent);
    SeaWater->SetMaterialPropertiesTable(fMediumOpticalProperties);
    fMapMaterial.insert({"Sea Water", SeaWater});
}

void MaterialManager::BuildIce()
{
    // build material component
    G4Material *Ice = new G4Material("Ice", 0.92 * g / cm3, 2);
    Ice->AddElement(fElH, 2);
    Ice->AddElement(fElO, 1);
    Ice->SetMaterialPropertiesTable(fMediumOpticalProperties);
    fMapMaterial.insert({"Ice", Ice});
}

void MaterialManager::BuildGlass()
{
    // build material component
    G4Material *Glass = new G4Material("Glass", 1.19 * g / cm3, 2);
    Glass->AddElement(fElSi, 1);
    Glass->AddElement(fElO, 2);

    // build optical property
    G4MaterialPropertiesTable *mpt = new G4MaterialPropertiesTable();
    const G4int num = 2;
    G4double photonEnergy[num] = {2.06667 * eV, 4.13333 * eV};
    G4double refractiveIndex[num] = {1.50, 1.50};
    G4double absorptionLength[num] = {10. * m, 10. * m};
    mpt->AddProperty("RINDEX", photonEnergy, refractiveIndex, num);
    mpt->AddProperty("ABSLENGTH", photonEnergy, absorptionLength, num);
    Glass->SetMaterialPropertiesTable(mpt);

    fMapMaterial.insert({"Glass", Glass});
}

void MaterialManager::BuildEpoxy()
{
    // build material component
    G4Material *Epoxy = new G4Material("Epoxy", 1.19 * g / cm3, 3);
    Epoxy->AddElement(fElC, 5);
    Epoxy->AddElement(fElH, 8);
    Epoxy->AddElement(fElO, 2);
    // no optical property, photon will be absorbed by Epoxy
    fMapMaterial.insert({"Epoxy", Epoxy});
}

void MaterialManager::BuildGel()
{
    // build material component
    G4Material *Gel = new G4Material("Gel", 1.20 * g / cm3, 3);
    Gel->AddElement(fElC, 4);
    Gel->AddElement(fElH, 8);
    Gel->AddElement(fElO, 2);

    // build optical property
    G4MaterialPropertiesTable *mpt = new G4MaterialPropertiesTable();
    const G4int num = 2;
    G4double photonEnergy[num] = {2.06667 * eV, 4.13333 * eV};
    G4double refractiveIndex[num] = {1.41, 1.41};  // SilGel 601 A/B by Wacker
    G4double absorptionLength[num] = {10. * m, 10. * m};
    mpt->AddProperty("RINDEX", photonEnergy, refractiveIndex, num);
    mpt->AddProperty("ABSLENGTH", photonEnergy, absorptionLength, num);
    Gel->SetMaterialPropertiesTable(mpt);

    fMapMaterial.insert({"Gel", Gel});
}

void MaterialManager::BuildScint()
{
    // build material component
    G4Material *Scint = new G4Material("Scint", 1.023 * g / cm3, 2);
    Scint->AddElement(fElC, 10);
    Scint->AddElement(fElH, 11);
    Scint->GetIonisation()->SetBirksConstant(0.126*mm/MeV);
    Scint->SetMaterialPropertiesTable(SetOpticalPropertiesOfPS());
    // no optical property, photon will be absorbed by Scint
    fMapMaterial.insert({"Scint", Scint});
}

void MaterialManager::BuildESR()
{
    G4Material* Warp = G4NistManager::Instance()->FindOrBuildMaterial("G4_POLYETHYLENE");
    fMapMaterial.insert({"ESR", Warp});
}

void MaterialManager::BuildTape()
{
    G4Material* Tape = G4NistManager::Instance()->FindOrBuildMaterial("G4_POLYETHYLENE");
    fMapMaterial.insert({"Tape", Tape});
}

void MaterialManager::BuildSiPM()
{
    // build material component
    G4Material *SiPM = new G4Material("SiPM", 1.20 * g / cm3, 2);
    SiPM->AddElement(fElSi, 1);
    SiPM->AddElement(fElO, 2);
    fMapMaterial.insert({"SiPM", SiPM});

    // build optical property
    // CRITICAL: To enable sensitive detector to detect photon hit,
    // we must set both RINDEX (for photons to enter) and ABSLENGTH (for absorption/detection)
    G4MaterialPropertiesTable *mpt = new G4MaterialPropertiesTable();

    const G4int num = 2;
    G4double photonEnergy[num] = {2.0 * eV, 4.0 * eV};  // 600nm - 300nm range

    // Refractive index for silicon (~1.5 for SiO2 coating on SiPM)
    G4double refractiveIndex[num] = {1.50, 1.50};

    // Absorption length: Set to 1.0 mm (roughly SiPM thickness)
    // This allows photons to take at least one step inside SiPM before being absorbed
    // CRITICAL: Must be long enough for ProcessHits() to trigger, but short enough for detection
    G4double absorptionLength[num] = {1.0 * mm, 1.0 * mm};

    mpt->AddProperty("RINDEX", photonEnergy, refractiveIndex, num);
    mpt->AddProperty("ABSLENGTH", photonEnergy, absorptionLength, num);

    // ========================================================================
    // PHASE 2.5: Load and Apply SiPM PDE (Photon Detection Efficiency)
    // ========================================================================
    // Load PDE from config file and add as EFFICIENCY property
    // Geant4 will automatically reject photons based on this efficiency
    auto config_node = rootNode["Property"];
    if (config_node && config_node["sipm"] && config_node["sipm"]["pde_file"]) {
        string pde_path = config_node["sipm"]["pde_file"].as<string>();
        logger->info("Loading SiPM PDE from: {}", pde_path);

        std::ifstream pde_file(pde_path);
        if (!pde_file.is_open()) {
            logger->warn("Failed to open SiPM PDE file: {}, using 100% efficiency", pde_path);
            // Use 100% efficiency as fallback
            G4double efficiency[num] = {1.0, 1.0};
            mpt->AddProperty("EFFICIENCY", photonEnergy, efficiency, num);
        } else {
            // Load PDE data: wavelength (nm) and efficiency (0-1)
            vector<G4double> wavelengths;
            vector<G4double> efficiencies;
            double wl, eff;

            while (pde_file >> wl >> eff) {
                wavelengths.push_back(wl);  // nm
                efficiencies.push_back(eff);  // already 0-1 range
            }
            pde_file.close();

            logger->info("Loaded {} PDE data points from {}", wavelengths.size(), pde_path);

            // Convert wavelength (nm) to energy (eV): E = 1240/lambda
            vector<G4double> pde_energies;
            vector<G4double> pde_efficiencies;

            for (size_t i = 0; i < wavelengths.size(); i++) {
                G4double energy_eV = 1240.0 / wavelengths[i];  // Convert nm to eV
                pde_energies.push_back(energy_eV * eV);
                pde_efficiencies.push_back(efficiencies[i]);
            }

            // Add EFFICIENCY property to material
            mpt->AddProperty("EFFICIENCY",
                           pde_energies.data(),
                           pde_efficiencies.data(),
                           pde_energies.size());

            // Log PDE at WLS emission peak (~490nm)
            // Find the PDE value closest to 490nm
            const G4double wls_peak_nm = 490.0;
            G4double pde_at_peak = 0.0;
            G4double min_diff = 999.0;
            for (size_t i = 0; i < wavelengths.size(); i++) {
                G4double diff = std::abs(wavelengths[i] - wls_peak_nm);
                if (diff < min_diff) {
                    min_diff = diff;
                    pde_at_peak = efficiencies[i];
                }
            }
            logger->info("SiPM PDE at WLS peak ({} nm) is approximately {:.1f}%",
                        wls_peak_nm,
                        pde_at_peak * 100.0);
        }
    } else {
        logger->warn("SiPM PDE file not specified in config, using 100% efficiency");
        G4double efficiency[num] = {1.0, 1.0};
        mpt->AddProperty("EFFICIENCY", photonEnergy, efficiency, num);
    }

    SiPM->SetMaterialPropertiesTable(mpt);

    fMapMaterial.insert({"SiPM", SiPM});
}

void MaterialManager::BuildBattery()
{
    G4Material* Battery = G4NistManager::Instance()->FindOrBuildMaterial("G4_Al");
    fMapMaterial.insert({"Battery", Battery});
}

G4MaterialPropertiesTable* MaterialManager::SetOpticalPropertiesOfPS()
{

    G4MaterialPropertiesTable* mptPlScin = new G4MaterialPropertiesTable();

    const G4int nEntries= 43;//301;//100;

	G4double EJ200_SCINT[nEntries];
	G4double EJ200_RIND[nEntries];
	G4double EJ200_ABSL[nEntries];
	G4double photonEnergy[nEntries];

	std::ifstream ReadEJ200;
	G4int ScintEntry=0;
	G4String filler;
	G4double pEnergy;
	G4double pWavelength;
	G4double pSEff;
    string pathFile = rootNode["Property"]["scintillator"]["spectrum_file"].as<string>();
	ReadEJ200.open(pathFile.c_str());
	if(ReadEJ200.is_open()){
    while(!ReadEJ200.eof()){
        ReadEJ200 >> pWavelength >> pSEff;
        pEnergy = (1240/pWavelength)*eV;
        photonEnergy[ScintEntry] = pEnergy;
        EJ200_SCINT[ScintEntry] = pSEff;
        if (spdlog::should_log(spdlog::level::debug)) {
            logger->debug("read-in energy scint: {:f} eff: {:f}", photonEnergy[ScintEntry], EJ200_SCINT[ScintEntry]);
        }
        ScintEntry++;
    }
	}
	else logger->error("Error opening file EJ200ScintSpectrum.txt");
	ReadEJ200.close();


	for (int i = 0; i < nEntries; i++) {
		EJ200_RIND[i] = 1.58;//58; // refractive index at 425 nm
		//EJ200_ABSL[i] *= myPSAttenuationLength;
		EJ200_ABSL[i] = 3.8*m;//2.5 * m; // bulk attenuation at 425 nm
	}

	mptPlScin->AddProperty("FASTCOMPONENT", photonEnergy, EJ200_SCINT,nEntries);//->SetSpline(true);


	mptPlScin->AddProperty("ABSLENGTH", photonEnergy, EJ200_ABSL,nEntries);//->SetSpline(true);

	mptPlScin->AddConstProperty("SCINTILLATIONYIELD", 10000.0 / MeV); //--- EJ-200: ~10,000 photons/MeV
	mptPlScin->AddConstProperty("RESOLUTIONSCALE", 1.0);
	mptPlScin->AddConstProperty("FASTTIMECONSTANT", 2.1 * ns); //decay time, according to EJ200
	mptPlScin->AddProperty("RINDEX", photonEnergy, EJ200_RIND, nEntries);//->SetSpline(true);

    return mptPlScin;
}

float *MaterialManager::GetArrayProperites()
{
    int num = fSeaOpticalProperty.num;
    float *propertis = new float [5*num];
    for (int i = 0; i < num; i++)
    {
        int idx = 5*i;
        propertis[idx+0] = fSeaOpticalProperty.refracIdxPhase[i];
        propertis[idx+1] = fSeaOpticalProperty.refracIdxGroup[i];
        propertis[idx+2] = fSeaOpticalProperty.absLen[i];
        propertis[idx+3] = fSeaOpticalProperty.scaLenMie[i];
        propertis[idx+4] = fSeaOpticalProperty.scaLenRay[i];
    }
    return propertis;
}

bool MaterialManager::LoadSpectrum(const std::string& filename,
                                    std::vector<G4double>& energies,
                                    std::vector<G4double>& intensities)
{
    logger->info("Loading spectrum from: {}", filename);

    std::ifstream file(filename);
    if (!file.is_open()) {
        logger->error("Failed to open spectrum file: {}", filename);
        return false;
    }

    energies.clear();
    intensities.clear();

    std::string line;
    std::vector<G4double> rawWavelengths;
    std::vector<G4double> rawIntensities;

    // Read all lines
    while (std::getline(file, line)) {
        // Skip empty lines
        if (line.empty()) continue;

        // Check for header line (contains non-numeric characters like "x,Curve" or "#")
        if (line[0] == '#' || line[0] == 'x' || line[0] == 'w') {
            continue;
        }

        // Try to parse as CSV (comma-separated)
        std::istringstream iss(line);
        char delimiter;
        G4double wavelength, intensity;

        // First try comma delimiter
        if (iss >> wavelength >> delimiter >> intensity) {
            if (delimiter == ',') {
                rawWavelengths.push_back(wavelength);
                rawIntensities.push_back(intensity);
                continue;
            }
        }

        // Try space/tab delimiter
        iss.clear();
        iss.str(line);
        if (iss >> wavelength >> intensity) {
            rawWavelengths.push_back(wavelength);
            rawIntensities.push_back(intensity);
        }
    }

    file.close();

    if (rawWavelengths.empty()) {
        logger->error("No data loaded from spectrum file: {}", filename);
        return false;
    }

    // Convert wavelength (nm) to energy (eV) and sort by energy (ascending)
    // E [eV] = 1239.841939 / lambda [nm]
    struct DataPoint {
        G4double energy;
        G4double intensity;
        bool operator<(const DataPoint& other) const { return energy < other.energy; }
    };

    std::vector<DataPoint> dataPoints;
    for (size_t i = 0; i < rawWavelengths.size(); ++i) {
        G4double energy = (1239.841939 / rawWavelengths[i]) * eV;
        dataPoints.push_back({energy, rawIntensities[i]});
    }

    // Sort by energy (ascending order)
    std::sort(dataPoints.begin(), dataPoints.end());

    // Extract sorted data
    for (const auto& point : dataPoints) {
        energies.push_back(point.energy);
        intensities.push_back(point.intensity);
    }

    logger->info("Loaded {} data points from spectrum file (energy range: {:.3f} - {:.3f} eV)",
                 energies.size(), energies.front()/eV, energies.back()/eV);
    return true;
}

void MaterialManager::BuildSP101()
{
    logger->info("Building SP101 scintillator material for MuonCube...");

    // SP101 is based on polystyrene (similar to EJ-200)
    // Density: 1.023 g/cm3 (typical for plastic scintillator)
    G4Material* SP101 = new G4Material("SP101", 1.023 * g / cm3, 2);
    SP101->AddElement(fElC, 10);  // Polystyrene: (C8H8)n simplified as C10H11
    SP101->AddElement(fElH, 11);

    // Set Birks constant for quenching
    SP101->GetIonisation()->SetBirksConstant(0.126 * mm / MeV);

    // Create optical properties table
    G4MaterialPropertiesTable* mptSP101 = new G4MaterialPropertiesTable();

    // Try to load spectrum from config file
    std::vector<G4double> energies;
    std::vector<G4double> scintSpectrum;
    std::string spectrumFile;

    bool spectrumLoaded = false;

    // Check if MuonCube spectrum file is specified in config
    if (rootNode["MuonCube"] && rootNode["MuonCube"]["spectrum_file"]) {
        spectrumFile = rootNode["MuonCube"]["spectrum_file"].as<std::string>();
        spectrumLoaded = LoadSpectrum(spectrumFile, energies, scintSpectrum);
    }

    // If no spectrum file or loading failed, use default values
    if (!spectrumLoaded) {
        logger->warn("Using default SP101 optical properties (no spectrum file)");

        // Default energy points (from 300nm to 600nm)
        const int nEntries = 11;
        G4double defaultEnergy[nEntries] = {
            2.066 * eV,  // 600 nm
            2.254 * eV,  // 550 nm
            2.480 * eV,  // 500 nm
            2.755 * eV,  // 450 nm
            2.952 * eV,  // 420 nm (peak emission)
            3.100 * eV,  // 400 nm
            3.263 * eV,  // 380 nm
            3.444 * eV,  // 360 nm
            3.647 * eV,  // 340 nm
            3.875 * eV,  // 320 nm
            4.133 * eV   // 300 nm
        };

        // Typical plastic scintillator emission spectrum (normalized)
        G4double defaultScint[nEntries] = {
            0.05, 0.15, 0.40, 0.85, 1.00, 0.80, 0.45, 0.20, 0.08, 0.03, 0.01
        };

        energies.assign(defaultEnergy, defaultEnergy + nEntries);
        scintSpectrum.assign(defaultScint, defaultScint + nEntries);
    }

    int nEntries = energies.size();

    // Refractive index (constant 1.58 for polystyrene-based scintillator)
    std::vector<G4double> rIndex(nEntries, 1.58);

    // Absorption length (210.0 cm as per specification)
    std::vector<G4double> absLength(nEntries, 210.0 * cm);

    // Add properties to table
    // Use both legacy and modern keys for maximum compatibility
    mptSP101->AddProperty("SCINTILLATIONCOMPONENT", energies.data(), scintSpectrum.data(), nEntries);
    mptSP101->AddProperty("FASTCOMPONENT", energies.data(), scintSpectrum.data(), nEntries);  // Legacy key
    mptSP101->AddProperty("RINDEX", energies.data(), rIndex.data(), nEntries);
    mptSP101->AddProperty("ABSLENGTH", energies.data(), absLength.data(), nEntries);

    // Scintillation properties (Phase 2.0 specification + compatibility fixes)
    mptSP101->AddConstProperty("SCINTILLATIONYIELD", 11136.0 / MeV);
    mptSP101->AddConstProperty("RESOLUTIONSCALE", 1.0);
    mptSP101->AddConstProperty("SCINTILLATIONTIMECONSTANT", 2.4 * ns);
    mptSP101->AddConstProperty("FASTTIMECONSTANT", 2.4 * ns);  // Legacy key
    mptSP101->AddConstProperty("SCINTILLATIONYIELD1", 1.0);  // Ratio of fast component

    SP101->SetMaterialPropertiesTable(mptSP101);

    fMapMaterial.insert({"SP101", SP101});

    logger->info("SP101 material built successfully (Phase 2.0)");
    logger->info("  Scintillation yield: 11,136 photons/MeV");
    logger->info("  Refractive index: 1.58");
    logger->info("  Absorption length: 210.0 cm");
    logger->info("  Scintillation time constant: 2.4 ns");
}

void MaterialManager::BuildBCF92_Core()
{
    logger->info("Building BCF-92 WLS Fiber Core material (Phase 2.0)...");

    // BCF-92 Core is based on polystyrene
    // Density: 1.05 g/cm3 (typical for polystyrene)
    G4Material* BCF92_Core = new G4Material("BCF92_Core", 1.05 * g / cm3, 2);
    BCF92_Core->AddElement(fElC, 10);  // Polystyrene: (C8H8)n
    BCF92_Core->AddElement(fElH, 11);

    // Create optical properties table
    G4MaterialPropertiesTable* mpt = new G4MaterialPropertiesTable();

    // ========================================================================
    // CRITICAL: Use DECOUPLED energy vectors for WLS Absorption and Emission
    // Geant4 allows different properties to have different energy grids
    // This prevents out-of-bounds access when spectrum files have different sizes
    // ========================================================================

    // WLS Absorption spectrum (independent energy grid)
    std::vector<G4double> absEnergies;
    std::vector<G4double> absValues;

    // WLS Emission spectrum (independent energy grid)
    std::vector<G4double> emitEnergies;
    std::vector<G4double> emitValues;

    bool wlsAbsLoaded = false;
    bool wlsEmitLoaded = false;

    // Load WLS Absorption spectrum
    if (rootNode["MuonCube"] && rootNode["MuonCube"]["wls_abs_file"]) {
        std::string absFile = rootNode["MuonCube"]["wls_abs_file"].as<std::string>();
        wlsAbsLoaded = LoadSpectrum(absFile, absEnergies, absValues);

        // ====================================================================
        // CRITICAL FIX: Convert amplitude to absorption length using inverse
        // ====================================================================
        // The spectrum file contains normalized amplitudes (0-1 range)
        // Physics: High amplitude = strong absorption = SHORT absorption length
        // Formula: AbsorptionLength = BaseLength / Amplitude
        //
        // For BCF-92, peak absorption at ~407nm should be ~1mm
        // ====================================================================

        const G4double baseAbsorptionLength = 1.0 * mm;  // Peak absorption length
        const G4double maxAbsorptionLength = 10.0 * m;   // Cap to avoid infinite values

        logger->info("  [SPECTRUM FIX] Converting absorption amplitudes to lengths...");
        logger->info("    Base length: {:.3f} mm", baseAbsorptionLength / mm);
        logger->info("    Max length cap: {:.3f} m", maxAbsorptionLength / m);

        for (size_t i = 0; i < absValues.size(); ++i) {
            G4double amplitude = absValues[i];

            // Avoid division by zero
            if (amplitude < 1e-6) {
                absValues[i] = maxAbsorptionLength;
            } else {
                // Inverse relationship: L = BaseLength / Amplitude
                G4double calcLength = baseAbsorptionLength / amplitude;

                // Cap at maximum
                absValues[i] = std::min(calcLength, maxAbsorptionLength);
            }
        }

        logger->info("    Conversion complete. Absorption length range:");
        logger->info("      Min: {:.3f} mm (peak absorption)",
                     *std::min_element(absValues.begin(), absValues.end()) / mm);
        logger->info("      Max: {:.3f} m (minimal absorption)",
                     *std::max_element(absValues.begin(), absValues.end()) / m);
    }

    // Load WLS Emission spectrum (separate energy grid - DO NOT merge)
    if (rootNode["MuonCube"] && rootNode["MuonCube"]["wls_emit_file"]) {
        std::string emitFile = rootNode["MuonCube"]["wls_emit_file"].as<std::string>();
        wlsEmitLoaded = LoadSpectrum(emitFile, emitEnergies, emitValues);
    }

    // If files not loaded, use default values
    if (!wlsAbsLoaded || !wlsEmitLoaded) {
        logger->warn("Using default BCF-92 Core WLS properties (spectrum files not loaded)");

        // Default energy points for absorption (from 360nm to 600nm)
        const int nAbs = 7;
        G4double defaultAbsEnergy[nAbs] = {
            2.066 * eV,  // 600 nm
            2.480 * eV,  // 500 nm
            2.755 * eV,  // 450 nm
            2.952 * eV,  // 420 nm
            3.100 * eV,  // 400 nm
            3.263 * eV,  // 380 nm
            3.444 * eV   // 360 nm
        };
        G4double defaultAbs[nAbs] = {0.02, 0.15, 0.50, 0.95, 0.80, 0.40, 0.15};

        absEnergies.assign(defaultAbsEnergy, defaultAbsEnergy + nAbs);
        absValues.assign(defaultAbs, defaultAbs + nAbs);

        // Default energy points for emission (peak at 492nm)
        const int nEmit = 7;
        G4double defaultEmitEnergy[nEmit] = {
            2.066 * eV,  // 600 nm
            2.480 * eV,  // 500 nm
            2.520 * eV,  // 492 nm (peak)
            2.755 * eV,  // 450 nm
            2.952 * eV,  // 420 nm
            3.100 * eV,  // 400 nm
            3.263 * eV   // 380 nm
        };
        G4double defaultEmit[nEmit] = {0.01, 0.25, 0.95, 0.85, 0.70, 0.30, 0.05};

        emitEnergies.assign(defaultEmitEnergy, defaultEmitEnergy + nEmit);
        emitValues.assign(defaultEmit, defaultEmit + nEmit);
    }

    // ========================================================================
    // CRITICAL FIX: Truncate WLS Absorption Spectrum to Prevent Self-Absorption
    // (Stokes Shift Fix)
    // ========================================================================
    // Physics Rule: BCF-92 absorbs Blue (<460nm) and emits Green (>490nm)
    // The green emitted light should NOT be re-absorbed by the WLS process
    //
    // Energy-Wavelength Conversion: E(eV) = 1240 / wavelength(nm)
    // Cutoff: 470 nm = 2.64 eV
    //
    // For energies < 2.64 eV (wavelengths > 470nm), set WLS absorption to LARGE value
    // This makes green light transparent to the WLS process
    //
    G4double cutoffEnergy = (1240.0 / 470.0) * eV;  // 2.64 eV (CRITICAL: * eV for unit consistency!)
    G4double transparentWLSAbs = 100.0 * m;  // Large but reasonable value (100 meters)

    int truncatedCount = 0;
    int nAbsPoints = absEnergies.size();

    // DEBUG: Print first and last values BEFORE truncation
    logger->info("  [DEBUG] Before truncation:");
    logger->info("    Energy range: {:.3f} - {:.3f} eV", absEnergies.front()/eV, absEnergies.back()/eV);
    logger->info("    Value range (first 3): {:.3f}, {:.3f}, {:.3f}",
                 absValues[0], absValues[1], absValues[2]);
    logger->info("    Value range (last 3): {:.3f}, {:.3f}, {:.3f}",
                 absValues[nAbsPoints-3], absValues[nAbsPoints-2], absValues[nAbsPoints-1]);
    logger->info("    Cutoff energy: {:.3f} eV (470 nm)", cutoffEnergy/eV);

    for (int i = 0; i < nAbsPoints; ++i) {
        if (absEnergies[i] < cutoffEnergy) {
            // Wavelength > 470nm: Make transparent to WLS process
            absValues[i] = transparentWLSAbs;
            truncatedCount++;
        }
    }

    logger->info("  WLS Absorption Truncation Applied:");
    logger->info("    Cutoff wavelength: 470 nm (2.64 eV)");
    logger->info("    Truncated " + std::to_string(truncatedCount) + " of " + std::to_string(nAbsPoints) + " absorption spectral points");
    logger->info("    Green light (>470nm) is now transparent to WLS process");

    // DEBUG: Print first and last values AFTER truncation
    logger->info("  [DEBUG] After truncation:");
    logger->info("    Value range (first 3): {:.3f}, {:.3f}, {:.3f}",
                 absValues[0], absValues[1], absValues[2]);
    logger->info("    Value range (last 3): {:.3f}, {:.3f}, {:.3f}",
                 absValues[nAbsPoints-3], absValues[nAbsPoints-2], absValues[nAbsPoints-1]);

    // ========================================================================
    // DIAGNOSTIC: Check WLS Absorption Length at 420nm (Blue Light)
    // ========================================================================
    // 420nm = 2.95 eV (peak absorption for BCF-92)
    // This value should be SMALL (< 1.0 mm) for efficient WLS conversion
    G4double targetEnergy = (1240.0 / 420.0) * eV;  // 2.95 eV - CRITICAL: multiply by eV unit!
    G4double wlsAbsAt420nm = 0.0;
    bool found420nm = false;

    // Use wider tolerance (0.1 eV) to find the data point
    // DEBUG: Print energy range
    logger->info("  [DEBUG] WLS Absorption spectrum: {} points, energy range: {:.3f} - {:.3f} eV",
                 nAbsPoints, absEnergies.front()/eV, absEnergies.back()/eV);
    logger->info("  [DEBUG] Looking for 420nm ({:.3f} eV) with tolerance 0.1 eV", targetEnergy/eV);

    for (int i = 0; i < nAbsPoints; ++i) {
        if (std::abs(absEnergies[i] - targetEnergy) < 0.1 * eV) {
            wlsAbsAt420nm = absValues[i];
            found420nm = true;

            // Convert to mm for display
            // NOTE: absValues are normalized (0-1 range) from spectrum file
            // These represent relative absorption probability, not physical length
            // Geant4 will interpret the numerical value as mm
            G4double wlsAbsMM = wlsAbsAt420nm / mm;

            logger->warn("  [DIAGNOSTIC] WLS Absorption Length at 420nm:");
            logger->warn("    Energy: {:.3f} eV ({:.1f} nm)", absEnergies[i]/eV, 1240.0/(absEnergies[i]/eV));
            logger->warn("    Raw value from file: {:.6f}", wlsAbsAt420nm);
            logger->warn("    WLSABSLENGTH (interpreted by Geant4): {:.6f} mm", wlsAbsMM);

            if (wlsAbsMM > 10.0) {
                logger->error("    ⚠️  CRITICAL: WLS absorption is TOO LONG (>10mm)!");
                logger->error("    Blue photons will pass through fiber without WLS conversion!");
                logger->error("    Check units: Should be normalized (0-1) or mm");
            } else if (wlsAbsMM < 0.01) {
                logger->error("    ⚠️  CRITICAL: WLS absorption is TOO SHORT (<0.01mm)!");
                logger->error("    This may be a unit error (cm instead of mm?)");
                logger->error("    Expected: 0.1-5.0 mm range for BCF-92");
            } else if (wlsAbsMM > 0.1 && wlsAbsMM < 5.0) {
                logger->info("    ✅ WLS absorption length is reasonable (0.1-5.0 mm)");
                logger->info("    Blue light will be efficiently absorbed and converted");
            } else {
                logger->warn("    ⚠️  WLS absorption is outside expected range");
            }
            break;
        }
    }

    if (!found420nm) {
        logger->error("  [DIAGNOSTIC] Could not find WLS absorption data near 420nm (2.95 eV)!");
        logger->error("    Energy range in file: {:.3f} - {:.3f} eV", absEnergies.front()/eV, absEnergies.back()/eV);
        logger->error("    This is CRITICAL - WLS will not work properly!");
    }

    // ========================================================================

    // Refractive index (constant 1.60 for polystyrene)
    // Use the absorption energy grid for RINDEX (it doesn't matter much)
    int nEntries = absEnergies.size();
    std::vector<G4double> rIndex(nEntries, 1.60);

    // Absorption length (3.5 m for BCF-92) - non-WLS absorption
    std::vector<G4double> absLength(nEntries, 3.5 * m);

    // Add properties to table with DECOUPLED energy vectors
    mpt->AddProperty("RINDEX", absEnergies.data(), rIndex.data(), nEntries);
    mpt->AddProperty("ABSLENGTH", absEnergies.data(), absLength.data(), nEntries);
    mpt->AddProperty("WLSABSLENGTH", absEnergies.data(), absValues.data(), nAbsPoints);
    mpt->AddProperty("WLSCOMPONENT", emitEnergies.data(), emitValues.data(), emitEnergies.size());

    // WLS properties (Phase 2.0 specification)
    // WLSMEANNUMBERPHOTONS = Quantum yield (0.8 for BCF-92)
    // This is the mean number of emitted photons per absorbed blue photon
    mpt->AddConstProperty("WLSTIMECONSTANT", 2.7 * ns);
    mpt->AddConstProperty("WLSMEANNUMBERPHOTONS", 0.8);

    BCF92_Core->SetMaterialPropertiesTable(mpt);

    fMapMaterial.insert({"BCF92_Core", BCF92_Core});

    logger->info("BCF-92 Core material built successfully (Phase 2.0)");
    logger->info("  Refractive index: 1.60");
    logger->info("  Absorption length: 3.5 m");
    logger->info("  WLS time constant: 2.7 ns");
}

void MaterialManager::BuildBCF92_Clad()
{
    logger->info("Building BCF-92 WLS Fiber Cladding material (Phase 2.0)...");

    // BCF-92 Cladding is based on PMMA (acrylic)
    // Chemical formula: C5O2H8 (simplified as C5H8O2)
    // Density: 1.18 g/cm3 (typical for PMMA)
    G4Material* BCF92_Clad = new G4Material("BCF92_Clad", 1.18 * g / cm3, 3);
    BCF92_Clad->AddElement(fElC, 5);
    BCF92_Clad->AddElement(fElH, 8);
    BCF92_Clad->AddElement(fElO, 2);

    // Create optical properties table
    G4MaterialPropertiesTable* mpt = new G4MaterialPropertiesTable();

    // Simple optical properties for cladding (effectively transparent)
    const int nEntries = 2;
    G4double photonEnergy[nEntries] = {2.066 * eV, 4.133 * eV};  // 600 nm - 300 nm
    G4double refractiveIndex[nEntries] = {1.49, 1.49};  // Constant for PMMA
    G4double absorptionLength[nEntries] = {10.0 * m, 10.0 * m};  // Effectively transparent

    mpt->AddProperty("RINDEX", photonEnergy, refractiveIndex, nEntries);
    mpt->AddProperty("ABSLENGTH", photonEnergy, absorptionLength, nEntries);

    BCF92_Clad->SetMaterialPropertiesTable(mpt);

    fMapMaterial.insert({"BCF92_Clad", BCF92_Clad});

    logger->info("BCF-92 Cladding material built successfully (Phase 2.0)");
    logger->info("  Refractive index: 1.49");
    logger->info("  Absorption length: 10.0 m (effectively transparent)");
}

void MaterialManager::BuildAirWithOptics()
{
    // CRITICAL FIX for Optical Physics
    // Geant4 kills optical photons at boundaries to materials without RINDEX
    // We must add RINDEX to G4_AIR to allow photon propagation

    logger->info("Building G4_AIR with optical properties (CRITICAL for optical physics)...");

    // Get or build G4_AIR from NIST database
    G4Material* air = G4NistManager::Instance()->FindOrBuildMaterial("G4_AIR");

    if (!air) {
        logger->error("Failed to get G4_AIR from NIST manager!");
        return;
    }

    // Create material properties table for air
    G4MaterialPropertiesTable* airMPT = new G4MaterialPropertiesTable();

    // Energy range: 2.0 - 3.5 eV (covers optical spectrum 350-600 nm)
    const int nEntries = 2;
    G4double photonEnergy[nEntries] = {2.0 * eV, 3.5 * eV};
    G4double rIndex[nEntries] = {1.0, 1.0};  // Air refractive index ~1.0
    G4double absLength[nEntries] = {100.0 * m, 100.0 * m};  // Effectively transparent

    airMPT->AddProperty("RINDEX", photonEnergy, rIndex, nEntries);
    airMPT->AddProperty("ABSLENGTH", photonEnergy, absLength, nEntries);

    // Attach MPT to G4_AIR
    air->SetMaterialPropertiesTable(airMPT);

    logger->info("G4_AIR optical properties added successfully");
    logger->info("  Refractive index: 1.0 (constant)");
    logger->info("  Absorption length: 100.0 m (transparent)");
    logger->info("  Energy range: 2.0 - 3.5 eV (350 - 600 nm)");
}