/**
 * Curiously Recurring Template Pattern (CRTP) for Meyers singleton
 *
 * The singleton class is implemented as follows:
 * 
 * #include <Util/Singleton.hpp>
 *
 * class SomeClass : public Singleton<SomeClass> {
 *   ...
 * private:
 *   // prevent creation, destruction
 *   SomeClass() { }
 *   ~SomeClass() { }
 *
 *   friend class Singleton<SomeClass>;
 * };
 */
#ifndef SINGLETON_HH
#define SINGLETON_HH

#include "memory"

template <typename T>
class Singleton
{
public:
    static std::shared_ptr<T> Instance()
    {
        static std::shared_ptr<T> instance{new T};
        return instance;
    }

    // Singleton Classes should not be copied. Removes move constructor and
    Singleton(const Singleton &) = delete;

    // Move assignment as well
    Singleton &operator=(const Singleton &) = delete;

protected:
    // derived class can call constructor and deconstructor
    Singleton() {}
    ~Singleton() {}
};

#endif