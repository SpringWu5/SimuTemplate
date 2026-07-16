#ifndef SteppingAction_h
#define SteppingAction_h 1

#include "G4UserSteppingAction.hh"
#include "globals.hh"
#include <map>
#include <string>
#include <vector>

class EventAction;

class SteppingAction : public G4UserSteppingAction
{
  public:
    SteppingAction(EventAction* eventAction = nullptr);
    virtual ~SteppingAction();

    virtual void UserSteppingAction(const G4Step*);

    // 输出光子统计信息
    void OutputPhotonStatistics(G4int eventID, G4int cerCount, G4int scintCount);

    // 输出最终统计信息
    void OutputFinalStatistics();

    // Get particle statistics
    const std::map<G4String, G4int>& GetParticleCount() const { return particleCount; }

  private:
    EventAction* fEventAction;

    // Counters
    G4int cerenkovCount;
    G4int scintillationCount;
    G4int wlsCount;  // WLS photon counter
    G4int currentEventID;

    // Per-run photon-statistics accumulators (instance-owned, not global)
    std::vector<int> fCerenkovCounts;
    std::vector<int> fScintillationCounts;

    // Particle counting map
    std::map<G4String, G4int> particleCount;
};

#endif
