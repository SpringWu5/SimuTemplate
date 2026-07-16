#pragma once

#include "nlohmann/json.hpp"
#include "vector"
using json = nlohmann::json;

// a representation of particle
// units used are meter for position, ns for time GeV for momentum
struct McParticle {
    int pdgid;
    float x;
    float y;
    float z;
    float t;
    float px;
    float py;
    float pz;
};

class McEvent {
public:
    McEvent() {}

    // forbid copy
    McEvent(McEvent &) = delete;
    McEvent &operator=(McEvent &) = delete;

    McEvent(McEvent &&e) {
        std::swap(particles_in, e.particles_in);
        std::swap(particles_out, e.particles_out);
        std::swap(particles_at_detector, e.particles_at_detector);
        weight_volume = e.weight_volume;
        weight_spectrum = e.weight_spectrum;
        weight_interaction = e.weight_interaction;
        weight_survival = e.weight_survival;
        weight = e.weight;
        event_id = e.event_id;
    }

    std::vector<McParticle> particles_in;
    std::vector<McParticle> particles_out;
    std::vector<McParticle> particles_at_detector;

    // unit of weights: cm, s, srd, GeV
    float weight_volume = 1.0;
    float weight_spectrum = 1.0;
    float weight_interaction = 1.0;
    float weight_survival = 1.0;
    float weight = 1.0;

    int event_id = 0;
};

    // json parse by https://github.com/nlohmann/json

    inline void to_json(json &j, const McParticle &p) {
        j = {
            {"pdgid", p.pdgid}, {"x", p.x},   {"y", p.y},   {"z", p.z},
            {"t", p.t},         {"px", p.px}, {"py", p.py}, {"pz", p.pz},
        };
    }

    inline void from_json(const json &j, McParticle &p) {
        j.at("pdgid").get_to(p.pdgid);
        j.at("x").get_to(p.x);
        j.at("y").get_to(p.y);
        j.at("z").get_to(p.z);
        j.at("t").get_to(p.t);
        j.at("px").get_to(p.px);
        j.at("py").get_to(p.py);
        j.at("pz").get_to(p.pz);
    }

    inline void to_json(json &j, const McEvent &e) {
        for (auto &p : e.particles_in) {
            j["particles_in"].push_back(p);
        }
        // for (auto &p : e.particles_out) {
        //     j["particles_out"].push_back(p);
        // }
        for (auto &p : e.particles_at_detector) {
            j["particles_at_detector"].push_back(p);
        }
        j["weights"] = {{"volume", e.weight_volume},
                        {"spectrum", e.weight_spectrum},
                        {"interaction", e.weight_interaction},
                        {"survival", e.weight_survival},
                        {"total", e.weight_interaction * e.weight_spectrum *
                                        e.weight_volume * e.weight_survival}};
        j["event_id"] = e.event_id;
    }

    inline void from_json(const json &j, McEvent &e) {
        for (const auto &p : j["particles_in"]) {
            e.particles_in.push_back(p.get<McParticle>());
        }
        // for (const auto &p : j["particles_out"]) {
        //     e.particles_out.push_back(p.get<McParticle>());
        //     e.particles_at_detector.push_back(p.get<McParticle>());
        // }
        for (const auto &p : j["particles_at_detector"]) {
            e.particles_at_detector.push_back(p.get<McParticle>());
        }
        // e.weight_volume = j["weights"]["volume"].get<double>();
        // e.weight_spectrum = j["weights"]["spectrum"].get<double>();
        // e.weight_interaction = j["weights"]["interaction"].get<double>();
        // e.weight_survival = j["weights"]["survival"].get<double>();
        // e.weight = j["weights"]["total"].get<double>();
        e.event_id = j["event_id"].get<int>();
    }
