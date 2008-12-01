/////////////////////////////////////////////////////////////////////////////
//
// (C) Copyright Ion Gaztanaga  2007
//
// Distributed under the Boost Software License, Version 1.0.
//    (See accompanying file LICENSE_1_0.txt or copy at
//          http://www.boost.org/LICENSE_1_0.txt)
//
// See http://www.boost.org/libs/intrusive for documentation.
//
/////////////////////////////////////////////////////////////////////////////

#ifndef BOOST_INTRUSIVE_FWD_HPP
#define BOOST_INTRUSIVE_FWD_HPP

#include <cstddef>
#include <boost/intrusive/link_mode.hpp>

/// @cond

//std predeclarations
namespace std{

template<class T>
struct equal_to;

template<class T>
struct less;

}  //namespace std{

namespace boost {

//Hash predeclaration
template<class T>
struct hash;

namespace intrusive {

struct none;

}  //namespace intrusive{
}  //namespace boost{

namespace boost {
namespace intrusive {

////////////////////////////
//     Node algorithms
////////////////////////////

//Algorithms predeclarations
template<class NodeTraits>
class circular_list_algorithms;

template<class NodeTraits>
class circular_slist_algorithms;

template<class NodeTraits>
class rbtree_algorithms;

////////////////////////////
//       Containers
////////////////////////////

//slist
template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   , class O5  = none
   >
class slist;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   >
class slist_base_hook;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   >
class slist_member_hook;

//list
template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   >
class list;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   >
class list_base_hook;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   >
class list_member_hook;

//rbtree/set/multiset
template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class rbtree;

template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class set;

template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class multiset;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class set_base_hook;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class set_member_hook;

//splaytree/splay_set/splay_multiset
template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class splaytree;

template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class splay_set;

template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class splay_multiset;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   >
class splay_set_base_hook;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   >
class splay_set_member_hook;

//avltree/avl_set/avl_multiset
template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class avltree;

template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class avl_set;

template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class avl_multiset;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class avl_set_base_hook;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class avl_set_member_hook;

//sgtree/sg_set/sg_multiset
template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class sgtree;

template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class sg_set;

template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class sg_multiset;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   >
class bs_set_base_hook;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   >
class bs_set_member_hook;

//hashtable/unordered_set/unordered_multiset
template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   , class O5  = none
   , class O6  = none
   , class O7  = none
   , class O8  = none
   , class O9  = none
   >
class hashtable;

template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   , class O5  = none
   , class O6  = none
   , class O7  = none
   , class O8  = none
   , class O9  = none
   >
class unordered_set;

template
   < class T
   , class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   , class O5  = none
   , class O6  = none
   , class O7  = none
   , class O8  = none
   , class O9  = none
   >
class unordered_multiset;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class unordered_set_base_hook;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   , class O4  = none
   >
class unordered_set_member_hook;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   >
class any_base_hook;

template
   < class O1  = none
   , class O2  = none
   , class O3  = none
   >
class any_member_hook;

}  //namespace intrusive {
}  //namespace boost {

/// @endcond

#endif   //#ifndef BOOST_INTRUSIVE_FWD_HPP
