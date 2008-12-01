//Copyright (c) 2006-2008 Emil Dotchevski and Reverge Studios, Inc.

//Distributed under the Boost Software License, Version 1.0. (See accompanying
//file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

#ifndef UUID_0552D49838DD11DD90146B8956D89593
#define UUID_0552D49838DD11DD90146B8956D89593

#include <boost/exception/exception.hpp>
#include <exception>
#include <string>

namespace
boost
    {
    inline
    std::string
    diagnostic_information( std::exception const & x )
        {
        if( exception const * be = dynamic_cast<exception const *>(&x) )
            return be->diagnostic_information();
        else
            return std::string("[ what: ") + x.what() + ", type: " + typeid(x).name() + " ]";
        }
    }

#endif
