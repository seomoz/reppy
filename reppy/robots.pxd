# Cython declarations

from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp cimport bool

cdef extern from "rep-cpp/include/directive.h" namespace "Rep":
    cpdef cppclass CppDirective "Rep::Directive":
        ctypedef size_t priority_t

        CppDirective(const string& line, bool allowed)
        priority_t priority() const
        bool match(const string& path) const
        bool allowed() const
        string str() const

cdef extern from "rep-cpp/include/agent.h" namespace "Rep":
    cpdef cppclass CppAgent "Rep::Agent":
        ctypedef float delay_t

        CppAgent()
        CppAgent& allow(const string& query)
        CppAgent& disallow(const string& query)
        CppAgent& delay(delay_t delay)
        delay_t delay() const
        const vector[CppDirective]& directives() const
        bool allowed(const string& path) const
        string str() const
        @staticmethod
        string escape(const string& query)

cdef extern from "rep-cpp/include/robots.h" namespace "Rep":
    cpdef cppclass CppRobots "Rep::Robots":
        CppRobots(const string& content) except +ValueError
        CppRobots& operator=(const CppRobots& other)
        const vector[string]& sitemaps() const
        const CppAgent& agent(const string& name) const
        bool allowed(const string& path, const string& name) const
        string str() const
        @staticmethod
        string robotsUrl(const string& url) except +ValueError
