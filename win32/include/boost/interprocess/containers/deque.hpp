/*
 *
 * Copyright (c) 1994
 * Hewlett-Packard Company
 *
 * Permission to use, copy, modify, distribute and sell this software
 * and its documentation for any purpose is hereby granted without fee,
 * provided that the above copyright notice appear in all copies and
 * that both that copyright notice and this permission notice appear
 * in supporting documentation.  Hewlett-Packard Company makes no
 * representations about the suitability of this software for any
 * purpose.  It is provided "as is" without express or implied warranty.
 *
 *
 * Copyright (c) 1996
 * Silicon Graphics Computer Systems, Inc.
 *
 * Permission to use, copy, modify, distribute and sell this software
 * and its documentation for any purpose is hereby granted without fee,
 * provided that the above copyright notice appear in all copies and
 * that both that copyright notice and this permission notice appear
 * in supporting documentation.  Silicon Graphics makes no
 * representations about the suitability of this software for any
 * purpose.  It is provided "as is" without express or implied warranty.
 *
 */
//////////////////////////////////////////////////////////////////////////////
//
// (C) Copyright Ion Gaztanaga 2005-2006. Distributed under the Boost
// Software License, Version 1.0. (See accompanying file
// LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//
// See http://www.boost.org/libs/interprocess for documentation.
//
//////////////////////////////////////////////////////////////////////////////
//
// This file comes from SGI's stl_deque.h and stl_uninitialized.h files. 
// Modified by Ion Gaztanaga 2005.
// Renaming, isolating and porting to generic algorithms. Pointer typedef 
// set to allocator::pointer to allow placing it in shared memory.
//
///////////////////////////////////////////////////////////////////////////////

#ifndef BOOST_INTERPROCESS_DEQUE_HPP
#define BOOST_INTERPROCESS_DEQUE_HPP

#if (defined _MSC_VER) && (_MSC_VER >= 1200)
#  pragma once
#endif

#include <boost/interprocess/detail/config_begin.hpp>
#include <boost/interprocess/detail/workaround.hpp>

#include <boost/interprocess/detail/utilities.hpp>
#include <boost/interprocess/detail/iterators.hpp>
#include <boost/interprocess/detail/algorithms.hpp>
#include <boost/interprocess/detail/min_max.hpp>
#include <boost/interprocess/detail/mpl.hpp>
#include <boost/interprocess/interprocess_fwd.hpp>
#include <iterator>
#include <cstddef>
#include <iterator>
#include <memory>
#include <algorithm>
#include <stdexcept>
#include <boost/detail/no_exceptions_support.hpp>
#include <boost/interprocess/detail/move_iterator.hpp>
#include <boost/interprocess/detail/move.hpp>
#include <boost/type_traits/has_trivial_destructor.hpp>

namespace boost {
namespace interprocess {

/// @cond
template <class T, class Alloc>
class deque;

// Note: this function is simply a kludge to work around several compilers'
//  bugs in handling constant expressions.
inline std::size_t deque_buf_size(std::size_t size) 
   {  return size < 512 ? std::size_t(512 / size) : std::size_t(1);  }

// Deque base class.  It has two purposes.  First, its constructor
//  and destructor allocate (but don't initialize) storage.  This makes
//  exception safety easier.
template <class T, class Alloc>
class deque_base
{
   public:
   typedef typename Alloc::value_type              val_alloc_val;
   typedef typename Alloc::pointer                 val_alloc_ptr;
   typedef typename Alloc::const_pointer           val_alloc_cptr;
   typedef typename Alloc::reference               val_alloc_ref;
   typedef typename Alloc::const_reference         val_alloc_cref;
   typedef typename Alloc::value_type              val_alloc_diff;
   typedef typename Alloc::template rebind
      <typename Alloc::pointer>::other             ptr_alloc_t;
   typedef typename ptr_alloc_t::value_type        ptr_alloc_val;
   typedef typename ptr_alloc_t::pointer           ptr_alloc_ptr;
   typedef typename ptr_alloc_t::const_pointer     ptr_alloc_cptr;
   typedef typename ptr_alloc_t::reference         ptr_alloc_ref;
   typedef typename ptr_alloc_t::const_reference   ptr_alloc_cref;
   typedef typename Alloc::template
      rebind<T>::other                             allocator_type;
   typedef allocator_type                          stored_allocator_type;

   protected:
   enum {   trivial_dctr_after_move = boost::has_trivial_destructor<val_alloc_val>::value   };

   typedef typename Alloc::template
      rebind<typename Alloc::pointer>::other map_allocator_type;

   val_alloc_ptr priv_allocate_node() 
      {  return this->alloc().allocate(deque_buf_size(sizeof(T)));  }

   void priv_deallocate_node(val_alloc_ptr p) 
      {  this->alloc().deallocate(p, deque_buf_size(sizeof(T)));  }

   ptr_alloc_ptr priv_allocate_map(std::size_t n) 
      { return this->ptr_alloc().allocate(n); }

   void priv_deallocate_map(ptr_alloc_ptr p, std::size_t n) 
      { this->ptr_alloc().deallocate(p, n); }

 public:
   // Class invariants:
   //  For any nonsingular iterator i:
   //    i.node is the address of an element in the map array.  The
   //      contents of i.node is a pointer to the beginning of a node.
   //    i.first == //(i.node) 
   //    i.last  == i.first + node_size
   //    i.cur is a pointer in the range [i.first, i.last).  NOTE:
   //      the implication of this is that i.cur is always a dereferenceable
   //      pointer, even if i is a past-the-end iterator.
   //  Start and Finish are always nonsingular iterators.  NOTE: this means
   //    that an empty deque must have one node, and that a deque
   //    with N elements, where N is the buffer size, must have two nodes.
   //  For every node other than start.node and finish.node, every element
   //    in the node is an initialized object.  If start.node == finish.node,
   //    then [start.cur, finish.cur) are initialized objects, and
   //    the elements outside that range are uninitialized storage.  Otherwise,
   //    [start.cur, start.last) and [finish.first, finish.cur) are initialized
   //    objects, and [start.first, start.cur) and [finish.cur, finish.last)
   //    are uninitialized storage.
   //  [map, map + map_size) is a valid, non-empty range.  
   //  [start.node, finish.node] is a valid range contained within 
   //    [map, map + map_size).  
   //  A pointer in the range [map, map + map_size) points to an allocated node
   //    if and only if the pointer is in the range [start.node, finish.node].
   class const_iterator 
      : public std::iterator<std::random_access_iterator_tag, 
                              val_alloc_val,  val_alloc_diff, 
                              val_alloc_cptr, val_alloc_cref>
   {
      public:
      static std::size_t s_buffer_size() { return deque_buf_size(sizeof(T)); }

      typedef std::random_access_iterator_tag   iterator_category;
      typedef val_alloc_val                     value_type;
      typedef val_alloc_cptr                    pointer;
      typedef val_alloc_cref                    reference;
      typedef std::size_t                       size_type;
      typedef std::ptrdiff_t                    difference_type;

      typedef ptr_alloc_ptr                     index_pointer;
      typedef const_iterator                    self_t;

      friend class deque<T, Alloc>;
      friend class deque_base<T, Alloc>;

      protected: 
      val_alloc_ptr  m_cur;
      val_alloc_ptr  m_first;
      val_alloc_ptr  m_last;
      index_pointer  m_node;

      public: 
      const_iterator(val_alloc_ptr x, index_pointer y) 
         : m_cur(x), m_first(*y),
           m_last(*y + s_buffer_size()), m_node(y) {}

      const_iterator() : m_cur(0), m_first(0), m_last(0), m_node(0) {}

      const_iterator(const const_iterator& x)
         : m_cur(x.m_cur),   m_first(x.m_first), 
           m_last(x.m_last), m_node(x.m_node) {}

      reference operator*() const 
         { return *this->m_cur; }

      pointer operator->() const 
         { return this->m_cur; }

      difference_type operator-(const self_t& x) const 
      {
         return difference_type(this->s_buffer_size()) * (this->m_node - x.m_node - 1) +
            (this->m_cur - this->m_first) + (x.m_last - x.m_cur);
      }

      self_t& operator++() 
      {
         ++this->m_cur;
         if (this->m_cur == this->m_last) {
            this->priv_set_node(this->m_node + 1);
            this->m_cur = this->m_first;
         }
         return *this; 
      }

      self_t operator++(int)  
      {
         self_t tmp = *this;
         ++*this;
         return tmp;
      }

      self_t& operator--() 
      {
         if (this->m_cur == this->m_first) {
            this->priv_set_node(this->m_node - 1);
            this->m_cur = this->m_last;
         }
         --this->m_cur;
         return *this;
      }

      self_t operator--(int) 
      {
         self_t tmp = *this;
         --*this;
         return tmp;
      }

      self_t& operator+=(difference_type n)
      {
         difference_type offset = n + (this->m_cur - this->m_first);
         if (offset >= 0 && offset < difference_type(this->s_buffer_size()))
            this->m_cur += n;
         else {
            difference_type node_offset =
            offset > 0 ? offset / difference_type(this->s_buffer_size())
                        : -difference_type((-offset - 1) / this->s_buffer_size()) - 1;
            this->priv_set_node(this->m_node + node_offset);
            this->m_cur = this->m_first + 
            (offset - node_offset * difference_type(this->s_buffer_size()));
         }
         return *this;
      }

      self_t operator+(difference_type n) const
         {  self_t tmp = *this; return tmp += n;  }

      self_t& operator-=(difference_type n) 
         { return *this += -n; }
       
      self_t operator-(difference_type n) const 
         {  self_t tmp = *this; return tmp -= n;  }

      reference operator[](difference_type n) const 
         { return *(*this + n); }

      bool operator==(const self_t& x) const 
         { return this->m_cur == x.m_cur; }

      bool operator!=(const self_t& x) const 
         { return !(*this == x); }

      bool operator<(const self_t& x) const 
      {
         return (this->m_node == x.m_node) ? 
            (this->m_cur < x.m_cur) : (this->m_node < x.m_node);
      }

      bool operator>(const self_t& x) const  
         { return x < *this; }

      bool operator<=(const self_t& x) const 
         { return !(x < *this); }

      bool operator>=(const self_t& x) const 
         { return !(*this < x); }

      void priv_set_node(index_pointer new_node) 
      {
         this->m_node = new_node;
         this->m_first = *new_node;
         this->m_last = this->m_first + difference_type(this->s_buffer_size());
      }

      friend const_iterator operator+(std::ptrdiff_t n, const const_iterator& x)
         {  return x + n;  }
   };

   //Deque iterator
   class iterator : public const_iterator
   {
      public:
      typedef std::random_access_iterator_tag   iterator_category;
      typedef val_alloc_val                     value_type;
      typedef ptr_alloc_ptr                     pointer;
      typedef val_alloc_ref                     reference;
      typedef std::size_t                       size_type;
      typedef std::ptrdiff_t                    difference_type;
      typedef ptr_alloc_ptr                     index_pointer;
      typedef const_iterator                    self_t;

      friend class deque<T, Alloc>;
      friend class deque_base<T, Alloc>;

      private:
      explicit iterator(const const_iterator& x) : const_iterator(x){}

      public:
      //Constructors
      iterator(val_alloc_ptr x, index_pointer y) : const_iterator(x, y){}
      iterator() : const_iterator(){}
      //iterator(const const_iterator &cit) : const_iterator(cit){}
      iterator(const iterator& x) : const_iterator(x){}

      //Pointer like operators
      reference operator*() const { return *this->m_cur; }
      pointer operator->() const { return this->m_cur; }

      reference operator[](difference_type n) const { return *(*this + n); }

      //Increment / Decrement
      iterator& operator++()  
         { this->const_iterator::operator++(); return *this;  }

      iterator operator++(int)
         { iterator tmp = *this; ++*this; return tmp; }
      
      iterator& operator--()
         {  this->const_iterator::operator--(); return *this;  }

      iterator operator--(int)
         {  iterator tmp = *this; --*this; return tmp; }

      // Arithmetic
      iterator& operator+=(difference_type off)
         {  this->const_iterator::operator+=(off); return *this;  }

      iterator operator+(difference_type off) const
         {  return iterator(this->const_iterator::operator+(off));  }

      friend iterator operator+(difference_type off, const iterator& right)
         {  return iterator(off+static_cast<const const_iterator &>(right)); }

      iterator& operator-=(difference_type off)
         {  this->const_iterator::operator-=(off); return *this;   }

      iterator operator-(difference_type off) const
         {  return iterator(this->const_iterator::operator-(off));  }

      difference_type operator-(const const_iterator& right) const
         {  return static_cast<const const_iterator&>(*this) - right;   }
   };

   deque_base(const allocator_type& a, std::size_t num_elements)
      :  members_(a)
   { this->priv_initialize_map(num_elements); }

   deque_base(const allocator_type& a) 
      :  members_(a)
   {}

   ~deque_base()
   {
      if (this->members_.m_map) {
         this->priv_destroy_nodes(this->members_.m_start.m_node, this->members_.m_finish.m_node + 1);
         this->priv_deallocate_map(this->members_.m_map, this->members_.m_map_size);
      }
   }
  
   protected:
   void priv_initialize_map(std::size_t num_elements)
   {
      std::size_t num_nodes = num_elements / deque_buf_size(sizeof(T)) + 1;

      this->members_.m_map_size = max_value((std::size_t) InitialMapSize, num_nodes + 2);
      this->members_.m_map = this->priv_allocate_map(this->members_.m_map_size);

      ptr_alloc_ptr nstart = this->members_.m_map + (this->members_.m_map_size - num_nodes) / 2;
      ptr_alloc_ptr nfinish = nstart + num_nodes;
          
      BOOST_TRY {
         this->priv_create_nodes(nstart, nfinish);
      }
      BOOST_CATCH(...){
         this->priv_deallocate_map(this->members_.m_map, this->members_.m_map_size);
         this->members_.m_map = 0;
         this->members_.m_map_size = 0;
         BOOST_RETHROW
      }
      BOOST_CATCH_END

      this->members_.m_start.priv_set_node(nstart);
      this->members_.m_finish.priv_set_node(nfinish - 1);
      this->members_.m_start.m_cur = this->members_.m_start.m_first;
      this->members_.m_finish.m_cur = this->members_.m_finish.m_first +
                     num_elements % deque_buf_size(sizeof(T));
   }

   void priv_create_nodes(ptr_alloc_ptr nstart, ptr_alloc_ptr nfinish)
   {
      ptr_alloc_ptr cur;
      BOOST_TRY {
         for (cur = nstart; cur < nfinish; ++cur)
            *cur = this->priv_allocate_node();
      }
      BOOST_CATCH(...){
         this->priv_destroy_nodes(nstart, cur);
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }

   void priv_destroy_nodes(ptr_alloc_ptr nstart, ptr_alloc_ptr nfinish)
   {
      for (ptr_alloc_ptr n = nstart; n < nfinish; ++n)
         this->priv_deallocate_node(*n);
   }

   enum { InitialMapSize = 8 };

   protected:
   struct members_holder
      :  public ptr_alloc_t
      ,  public allocator_type
   {
      members_holder(const allocator_type &a)
         :  map_allocator_type(a), allocator_type(a)
         ,  m_map(0), m_map_size(0)
         ,  m_start(), m_finish()
      {}

      ptr_alloc_ptr   m_map;
      std::size_t     m_map_size;
      iterator        m_start;
      iterator        m_finish;
   } members_;

   ptr_alloc_t &ptr_alloc() 
   {  return members_;  }
   
   const ptr_alloc_t &ptr_alloc() const 
   {  return members_;  }

   allocator_type &alloc() 
   {  return members_;  }
   
   const allocator_type &alloc() const 
   {  return members_;  }
};
/// @endcond

//! Deque class
//!
template <class T, class Alloc>
class deque : protected deque_base<T, Alloc>
{
   /// @cond
  typedef deque_base<T, Alloc> Base;

   public:                         // Basic types
   typedef typename Alloc::value_type           val_alloc_val;
   typedef typename Alloc::pointer              val_alloc_ptr;
   typedef typename Alloc::const_pointer        val_alloc_cptr;
   typedef typename Alloc::reference            val_alloc_ref;
   typedef typename Alloc::const_reference      val_alloc_cref;
   typedef typename Alloc::template
      rebind<val_alloc_ptr>::other                ptr_alloc_t;
   typedef typename ptr_alloc_t::value_type       ptr_alloc_val;
   typedef typename ptr_alloc_t::pointer          ptr_alloc_ptr;
   typedef typename ptr_alloc_t::const_pointer    ptr_alloc_cptr;
   typedef typename ptr_alloc_t::reference        ptr_alloc_ref;
   typedef typename ptr_alloc_t::const_reference  ptr_alloc_cref;
   /// @endcond

   typedef T                                    value_type;
   typedef val_alloc_ptr                        pointer;
   typedef val_alloc_cptr                       const_pointer;
   typedef val_alloc_ref                        reference;
   typedef val_alloc_cref                       const_reference;
   typedef std::size_t                          size_type;
   typedef std::ptrdiff_t                       difference_type;

   typedef typename Base::allocator_type        allocator_type;

   public:                                // Iterators
   typedef typename Base::iterator              iterator;
   typedef typename Base::const_iterator        const_iterator;

   typedef std::reverse_iterator<const_iterator> const_reverse_iterator;
   typedef std::reverse_iterator<iterator>      reverse_iterator;

   /// @cond
   protected:                      // Internal typedefs
   typedef ptr_alloc_ptr index_pointer;
   static std::size_t s_buffer_size() 
         { return deque_buf_size(sizeof(T)); }
   /// @endcond

   allocator_type get_allocator() const { return Base::alloc(); }

   public:                         // Basic accessors
   iterator begin() 
      { return this->members_.m_start; }

   iterator end() 
      { return this->members_.m_finish; }

   const_iterator begin() const 
      { return this->members_.m_start; }

   const_iterator end() const 
      { return this->members_.m_finish; }

   reverse_iterator rbegin() 
      { return reverse_iterator(this->members_.m_finish); }

   reverse_iterator rend() 
      { return reverse_iterator(this->members_.m_start); }

   const_reverse_iterator rbegin() const 
      { return const_reverse_iterator(this->members_.m_finish); }

   const_reverse_iterator rend() const 
      { return const_reverse_iterator(this->members_.m_start); }

   reference operator[](size_type n)
      { return this->members_.m_start[difference_type(n)]; }

   const_reference operator[](size_type n) const 
      { return this->members_.m_start[difference_type(n)]; }

   void priv_range_check(size_type n) const 
      {  if (n >= this->size())  BOOST_RETHROW std::out_of_range("deque");   }

   reference at(size_type n)
      { this->priv_range_check(n); return (*this)[n]; }

   const_reference at(size_type n) const
      { this->priv_range_check(n); return (*this)[n]; }

   reference front() { return *this->members_.m_start; }

   reference back() 
   {
      iterator tmp = this->members_.m_finish;
      --tmp;
      return *tmp;
   }

   const_reference front() const 
      { return *this->members_.m_start; }

   const_reference back() const 
      {  const_iterator tmp = this->members_.m_finish;  --tmp;   return *tmp;  }

   size_type size() const 
      { return this->members_.m_finish - this->members_.m_start; }

   size_type max_size() const 
      { return this->alloc().max_size(); }

   bool empty() const 
      { return this->members_.m_finish == this->members_.m_start; }

   explicit deque(const allocator_type& a = allocator_type()) 
      : Base(a, 0) {}

   deque(const deque& x)
      :  Base(x.alloc(), x.size()) 
   { std::uninitialized_copy(x.begin(), x.end(), this->members_.m_start); }

   #ifndef BOOST_INTERPROCESS_RVALUE_REFERENCE
   deque(const detail::moved_object<deque> &mx) 
      :  Base(mx.get())
   {  this->swap(mx.get());   }
   #else
   deque(deque &&x) 
      :  Base(detail::move_impl(x))
   {  this->swap(x);   }
   #endif

   deque(size_type n, const value_type& value,
         const allocator_type& a = allocator_type()) : Base(a, n)
   { this->priv_fill_initialize(value); }

   explicit deque(size_type n) : Base(allocator_type(), n)
   {  this->resize(n); }

   // Check whether it's an integral type.  If so, it's not an iterator.
   template <class InpIt>
   deque(InpIt first, InpIt last,
         const allocator_type& a = allocator_type()) : Base(a) 
   {
      //Dispatch depending on integer/iterator
      const bool aux_boolean = detail::is_convertible<InpIt, std::size_t>::value;
      typedef detail::bool_<aux_boolean> Result;
      this->priv_initialize_dispatch(first, last, Result());
   }

   ~deque() 
   { priv_destroy_range(this->members_.m_start, this->members_.m_finish); }

   deque& operator= (const deque& x) 
   {
      const size_type len = size();
      if (&x != this) {
         if (len >= x.size())
            this->erase(std::copy(x.begin(), x.end(), this->members_.m_start), this->members_.m_finish);
         else {
            const_iterator mid = x.begin() + difference_type(len);
            std::copy(x.begin(), mid, this->members_.m_start);
            this->insert(this->members_.m_finish, mid, x.end());
         }
      }
      return *this;
   }        

   #ifndef BOOST_INTERPROCESS_RVALUE_REFERENCE
   deque& operator= (const detail::moved_object<deque> &mx) 
   {  this->clear(); this->swap(mx.get());   return *this;  }
   #else
   deque& operator= (deque &&mx) 
   {  this->clear(); this->swap(mx);   return *this;  }
   #endif

   void swap(deque& x)
   {
      std::swap(this->members_.m_start, x.members_.m_start);
      std::swap(this->members_.m_finish, x.members_.m_finish);
      std::swap(this->members_.m_map, x.members_.m_map);
      std::swap(this->members_.m_map_size, x.members_.m_map_size);
   }

   #ifndef BOOST_INTERPROCESS_RVALUE_REFERENCE
   void swap(const detail::moved_object<deque> &mx)
   {  this->swap(mx.get());   }
   #else
   void swap(deque &&mx)
   {  this->swap(mx);   }
   #endif

   void assign(size_type n, const T& val)
   {  this->priv_fill_assign(n, val);  }

   template <class InpIt>
   void assign(InpIt first, InpIt last) {
      //Dispatch depending on integer/iterator
      const bool aux_boolean = detail::is_convertible<InpIt, std::size_t>::value;
      typedef detail::bool_<aux_boolean> Result;
      this->priv_assign_dispatch(first, last, Result());
   }

   void push_back(const value_type& t) 
   {
      if (this->members_.m_finish.m_cur != this->members_.m_finish.m_last - 1) {
         new((void*)detail::get_pointer(this->members_.m_finish.m_cur))value_type(t);
         ++this->members_.m_finish.m_cur;
      }
      else
         this->priv_push_back_aux(t);
   }

   #ifndef BOOST_INTERPROCESS_RVALUE_REFERENCE
   void push_back(const detail::moved_object<value_type> &mt) 
   {
      if (this->members_.m_finish.m_cur != this->members_.m_finish.m_last - 1) {
         new((void*)detail::get_pointer(this->members_.m_finish.m_cur))value_type(mt);
         ++this->members_.m_finish.m_cur;
      }
      else
         this->priv_push_back_aux(mt);
   }
   #else
   void push_back(value_type &&mt) 
   {
      if (this->members_.m_finish.m_cur != this->members_.m_finish.m_last - 1) {
         new((void*)detail::get_pointer(this->members_.m_finish.m_cur))value_type(detail::move_impl(mt));
         ++this->members_.m_finish.m_cur;
      }
      else
         this->priv_push_back_aux(detail::move_impl(mt));
   }
   #endif

   void push_front(const value_type& t)
   {
      if (this->members_.m_start.m_cur != this->members_.m_start.m_first) {
         new((void*)(detail::get_pointer(this->members_.m_start.m_cur)- 1))value_type(t);
         --this->members_.m_start.m_cur;
      }
      else
         this->priv_push_front_aux(t);
   }

   #ifndef BOOST_INTERPROCESS_RVALUE_REFERENCE
   void push_front(const detail::moved_object<value_type> &mt)
   {
      if (this->members_.m_start.m_cur != this->members_.m_start.m_first) {
         new((void*)(detail::get_pointer(this->members_.m_start.m_cur)- 1))value_type(mt);
         --this->members_.m_start.m_cur;
      }
      else
         this->priv_push_front_aux(mt);
   }
   #else
   void push_front(value_type &&mt)
   {
      if (this->members_.m_start.m_cur != this->members_.m_start.m_first) {
         new((void*)(detail::get_pointer(this->members_.m_start.m_cur)- 1))value_type(detail::move_impl(mt));
         --this->members_.m_start.m_cur;
      }
      else
         this->priv_push_front_aux(detail::move_impl(mt));
   }
   #endif

   void pop_back() 
   {
      if (this->members_.m_finish.m_cur != this->members_.m_finish.m_first) {
         --this->members_.m_finish.m_cur;
         detail::get_pointer(this->members_.m_finish.m_cur)->~value_type();
      }
      else
         this->priv_pop_back_aux();
   }

   void pop_front() 
   {
      if (this->members_.m_start.m_cur != this->members_.m_start.m_last - 1) {
         detail::get_pointer(this->members_.m_start.m_cur)->~value_type();
         ++this->members_.m_start.m_cur;
      }
      else 
         this->priv_pop_front_aux();
   }

   iterator insert(iterator position, const value_type& x) 
   {
      if (position.m_cur == this->members_.m_start.m_cur) {
         this->push_front(x);
         return this->members_.m_start;
      }
      else if (position.m_cur == this->members_.m_finish.m_cur) {
         this->push_back(x);
         iterator tmp = this->members_.m_finish;
         --tmp;
         return tmp;
      }
      else {
         return this->priv_insert_aux(position, x);
      }
   }

   #ifndef BOOST_INTERPROCESS_RVALUE_REFERENCE
   iterator insert(iterator position, const detail::moved_object<value_type> &mx) 
   {
      if (position.m_cur == this->members_.m_start.m_cur) {
         this->push_front(mx);
         return this->members_.m_start;
      }
      else if (position.m_cur == this->members_.m_finish.m_cur) {
         this->push_back(mx);
         iterator tmp = this->members_.m_finish;
         --tmp;
         return tmp;
      }
      else {
         return this->priv_insert_aux(position, mx);
      }
   }
   #else
   iterator insert(iterator position, value_type &&mx) 
   {
      if (position.m_cur == this->members_.m_start.m_cur) {
         this->push_front(detail::move_impl(mx));
         return this->members_.m_start;
      }
      else if (position.m_cur == this->members_.m_finish.m_cur) {
         this->push_back(detail::move_impl(mx));
         iterator tmp = this->members_.m_finish;
         --tmp;
         return tmp;
      }
      else {
         return this->priv_insert_aux(position, detail::move_impl(mx));
      }
   }
   #endif

   void insert(iterator pos, size_type n, const value_type& x)
      { this->priv_fill_insert(pos, n, x); }

   // Check whether it's an integral type.  If so, it's not an iterator.
   template <class InpIt>
   void insert(iterator pos, InpIt first, InpIt last) 
   {
      //Dispatch depending on integer/iterator
      const bool aux_boolean = detail::is_convertible<InpIt, std::size_t>::value;
      typedef detail::bool_<aux_boolean> Result;
      this->priv_insert_dispatch(pos, first, last, Result());
   }

   void resize(size_type new_size, const value_type& x) 
   {
      const size_type len = size();
      if (new_size < len) 
         this->erase(this->members_.m_start + new_size, this->members_.m_finish);
      else
         this->insert(this->members_.m_finish, new_size - len, x);
   }

   void resize(size_type new_size) 
   {
      const size_type len = size();
      if (new_size < len) 
         this->erase(this->members_.m_start + new_size, this->members_.m_finish);
      else{
         size_type n = new_size - this->size();
         this->priv_reserve_elements_at_back(new_size);

         while(n--){
            //T default_constructed = detail::move_impl(T());
            T default_constructed;
/*            if(boost::is_scalar<T>::value){
               //Value initialization
               new(&default_constructed)T();
            }*/
            this->push_back(detail::move_impl(default_constructed));
         }
      }
   }

   iterator erase(iterator pos) 
   {
      iterator next = pos;
      ++next;
      difference_type index = pos - this->members_.m_start;
      if (size_type(index) < (this->size() >> 1)) {
         std::copy_backward( detail::make_move_iterator(this->members_.m_start)
                           , detail::make_move_iterator(pos)
                           , next);
         pop_front();
      }
      else {
         std::copy( detail::make_move_iterator(next)
                  , detail::make_move_iterator(this->members_.m_finish)
                  , pos);
         pop_back();
      }
      return this->members_.m_start + index;
   }

   iterator erase(iterator first, iterator last)
   {
      if (first == this->members_.m_start && last == this->members_.m_finish) {
         this->clear();
         return this->members_.m_finish;
      }
      else {
         difference_type n = last - first;
         difference_type elems_before = first - this->members_.m_start;
         if (elems_before < static_cast<difference_type>(this->size() - n) - elems_before) {
            std::copy_backward( detail::make_move_iterator(this->members_.m_start)
                              , detail::make_move_iterator(first)
                              , last);
            iterator new_start = this->members_.m_start + n;
            if(!Base::trivial_dctr_after_move)
               this->priv_destroy_range(this->members_.m_start, new_start);
            this->priv_destroy_nodes(new_start.m_node, this->members_.m_start.m_node);
            this->members_.m_start = new_start;
         }
         else {
            std::copy( detail::make_move_iterator(last)
                     , detail::make_move_iterator(this->members_.m_finish)
                     , first);
            iterator new_finish = this->members_.m_finish - n;
            if(!Base::trivial_dctr_after_move)
               this->priv_destroy_range(new_finish, this->members_.m_finish);
            this->priv_destroy_nodes(new_finish.m_node + 1, this->members_.m_finish.m_node + 1);
            this->members_.m_finish = new_finish;
         }
         return this->members_.m_start + elems_before;
      }
   }

   void clear()
   {
      for (index_pointer node = this->members_.m_start.m_node + 1;
            node < this->members_.m_finish.m_node;
            ++node) {
         this->priv_destroy_range(*node, *node + this->s_buffer_size());
         this->priv_deallocate_node(*node);
      }

      if (this->members_.m_start.m_node != this->members_.m_finish.m_node) {
         this->priv_destroy_range(this->members_.m_start.m_cur, this->members_.m_start.m_last);
         this->priv_destroy_range(this->members_.m_finish.m_first, this->members_.m_finish.m_cur);
         this->priv_deallocate_node(this->members_.m_finish.m_first);
      }
      else
         this->priv_destroy_range(this->members_.m_start.m_cur, this->members_.m_finish.m_cur);

      this->members_.m_finish = this->members_.m_start;
   }

   /// @cond
   private:

   template <class InpIt>
   void insert(iterator pos, InpIt first, InpIt last, std::input_iterator_tag)
   {  std::copy(first, last, std::inserter(*this, pos));  }

   template <class FwdIt>
   void insert(iterator pos, FwdIt first, FwdIt last, std::forward_iterator_tag) 
   {
      
      size_type n = 0;
      n = std::distance(first, last);

      if (pos.m_cur == this->members_.m_start.m_cur) {
         iterator new_start = this->priv_reserve_elements_at_front(n);
         BOOST_TRY{
            std::uninitialized_copy(first, last, new_start);
            this->members_.m_start = new_start;
         }
         BOOST_CATCH(...){
            this->priv_destroy_nodes(new_start.m_node, this->members_.m_start.m_node);
            BOOST_RETHROW
         }
         BOOST_CATCH_END
      }
      else if (pos.m_cur == this->members_.m_finish.m_cur) {
         iterator new_finish = this->priv_reserve_elements_at_back(n);
         BOOST_TRY{
            std::uninitialized_copy(first, last, this->members_.m_finish);
            this->members_.m_finish = new_finish;
         }
         BOOST_CATCH(...){
            this->priv_destroy_nodes(this->members_.m_finish.m_node + 1, new_finish.m_node + 1);
            BOOST_RETHROW
         }
         BOOST_CATCH_END
      }
      else
         this->priv_insert_aux(pos, first, last, n);
   }

  // assign(), a generalized assignment member function.  Two
  // versions: one that takes a count, and one that takes a range.
  // The range version is a member template, so we dispatch on whether
  // or not the type is an integer.
   void priv_fill_assign(size_type n, const T& val) {
      if (n > size()) {
         std::fill(begin(), end(), val);
         this->insert(end(), n - size(), val);
      }
      else {
         this->erase(begin() + n, end());
         std::fill(begin(), end(), val);
      }
   }

   template <class Integer>
   void priv_initialize_dispatch(Integer n, Integer x, detail::true_) 
   {
      this->priv_initialize_map(n);
      this->priv_fill_initialize(x);
   }

   template <class InpIt>
   void priv_initialize_dispatch(InpIt first, InpIt last, detail::false_) 
   {
      typedef typename std::iterator_traits<InpIt>::iterator_category ItCat;
      this->priv_range_initialize(first, last, ItCat());
   }

   void priv_destroy_range(iterator p, iterator p2)
   {
      for(;p != p2; ++p)
         detail::get_pointer(&*p)->~value_type();
   }

   void priv_destroy_range(pointer p, pointer p2)
   {
      for(;p != p2; ++p)
         detail::get_pointer(&*p)->~value_type();
   }

   template <class Integer>
   void priv_assign_dispatch(Integer n, Integer val, detail::true_)
      { this->priv_fill_assign((size_type) n, (T) val); }

   template <class InpIt>
   void priv_assign_dispatch(InpIt first, InpIt last, detail::false_) 
   {
      typedef typename std::iterator_traits<InpIt>::iterator_category ItCat;
      this->priv_assign_aux(first, last, ItCat());
   }

   template <class InpIt>
   void priv_assign_aux(InpIt first, InpIt last, std::input_iterator_tag)
   {
      iterator cur = begin();
      for ( ; first != last && cur != end(); ++cur, ++first)
         *cur = *first;
      if (first == last)
         this->erase(cur, end());
      else
         this->insert(end(), first, last);
   }

   template <class FwdIt>
   void priv_assign_aux(FwdIt first, FwdIt last,
                        std::forward_iterator_tag) {
      size_type len = 0;
      std::distance(first, last, len);
      if (len > size()) {
         FwdIt mid = first;
         std::advance(mid, size());
         std::copy(first, mid, begin());
         this->insert(end(), mid, last);
      }
      else
         this->erase(std::copy(first, last, begin()), end());
   }

   template <class Integer>
   void priv_insert_dispatch(iterator pos, Integer n, Integer x,
                           detail::true_) 
   {
      this->priv_fill_insert(pos, (size_type) n, (value_type) x);
   }

   template <class InpIt>
   void priv_insert_dispatch(iterator pos,
                           InpIt first, InpIt last,
                           detail::false_) 
   {
      typedef typename std::iterator_traits<InpIt>::iterator_category ItCat;
      this->insert(pos, first, last, ItCat());
   }

   iterator priv_insert_aux(iterator pos, const value_type& x)
   {
      size_type n = pos - begin();
      this->priv_insert_aux(pos, size_type(1), x);
      return iterator(this->begin() + n);
   }

   #ifndef BOOST_INTERPROCESS_RVALUE_REFERENCE
   iterator priv_insert_aux(iterator pos, const detail::moved_object<value_type> &mx)
   {
      typedef repeat_iterator<T, difference_type> r_iterator;
      typedef detail::move_iterator<r_iterator> move_it;
      //Just call more general insert(pos, size, value) and return iterator
      size_type n = pos - begin();
      this->insert(pos
                  ,move_it(r_iterator(mx.get(), 1))
                  ,move_it(r_iterator()));
      return iterator(this->begin() + n);
   }
   #else
   iterator priv_insert_aux(iterator pos, value_type &&mx)
   {
      typedef repeat_iterator<T, difference_type> r_iterator;
      typedef detail::move_iterator<r_iterator> move_it;
      //Just call more general insert(pos, size, value) and return iterator
      size_type n = pos - begin();
      this->insert(pos
                  ,move_it(r_iterator(mx, 1))
                  ,move_it(r_iterator()));
      return iterator(this->begin() + n);
   }
   #endif

   void priv_insert_aux(iterator pos, size_type n, const value_type& x)
   {
      typedef constant_iterator<value_type, difference_type> c_it;
      this->insert(pos, c_it(x, n), c_it());
   }

   template <class FwdIt>
   void priv_insert_aux(iterator pos, FwdIt first, FwdIt last, size_type n)
   {
      const difference_type elemsbefore = pos - this->members_.m_start;
      size_type length = size();
      if (elemsbefore < static_cast<difference_type>(length / 2)) {
         iterator new_start = this->priv_reserve_elements_at_front(n);
         iterator old_start = this->members_.m_start;
         pos = this->members_.m_start + elemsbefore;
         BOOST_TRY {
            if (elemsbefore >= difference_type(n)) {
               iterator start_n = this->members_.m_start + difference_type(n); 
               std::uninitialized_copy(detail::make_move_iterator(this->members_.m_start), detail::make_move_iterator(start_n), new_start);
               this->members_.m_start = new_start;
               std::copy(detail::make_move_iterator(start_n), detail::make_move_iterator(pos), old_start);
               std::copy(first, last, pos - difference_type(n));
            }
            else {
               FwdIt mid = first;
               std::advance(mid, difference_type(n) - elemsbefore);
               this->priv_uninitialized_copy_copy
                  (detail::make_move_iterator(this->members_.m_start), detail::make_move_iterator(pos), first, mid, new_start);
               this->members_.m_start = new_start;
               std::copy(mid, last, old_start);
            }
         }
         BOOST_CATCH(...){
            this->priv_destroy_nodes(new_start.m_node, this->members_.m_start.m_node);
            BOOST_RETHROW
         }
         BOOST_CATCH_END
      }
      else {
         iterator new_finish = this->priv_reserve_elements_at_back(n);
         iterator old_finish = this->members_.m_finish;
         const difference_type elemsafter = 
            difference_type(length) - elemsbefore;
         pos = this->members_.m_finish - elemsafter;
         BOOST_TRY {
            if (elemsafter > difference_type(n)) {
               iterator finish_n = this->members_.m_finish - difference_type(n);
               std::uninitialized_copy(detail::make_move_iterator(finish_n), detail::make_move_iterator(this->members_.m_finish), this->members_.m_finish);
               this->members_.m_finish = new_finish;
               std::copy_backward(detail::make_move_iterator(pos), detail::make_move_iterator(finish_n), old_finish);
               std::copy(first, last, pos);
            }
            else {
               FwdIt mid = first;
               std::advance(mid, elemsafter);
               this->priv_uninitialized_copy_copy(mid, last, detail::make_move_iterator(pos), detail::make_move_iterator(this->members_.m_finish), this->members_.m_finish);
               this->members_.m_finish = new_finish;
               std::copy(first, mid, pos);
            }
         }
         BOOST_CATCH(...){
            this->priv_destroy_nodes(this->members_.m_finish.m_node + 1, new_finish.m_node + 1);
            BOOST_RETHROW
         }
         BOOST_CATCH_END
      }
   }

   void priv_fill_insert(iterator pos, size_type n, const value_type& x)
   {
      typedef constant_iterator<value_type, difference_type> c_it;
      this->insert(pos, c_it(x, n), c_it());
   }

   // Precondition: this->members_.m_start and this->members_.m_finish have already been initialized,
   // but none of the deque's elements have yet been constructed.
   void priv_fill_initialize(const value_type& value) 
   {
      index_pointer cur;
      BOOST_TRY {
         for (cur = this->members_.m_start.m_node; cur < this->members_.m_finish.m_node; ++cur){
            std::uninitialized_fill(*cur, *cur + this->s_buffer_size(), value);
         }
         std::uninitialized_fill(this->members_.m_finish.m_first, this->members_.m_finish.m_cur, value);
      }
      BOOST_CATCH(...){
         this->priv_destroy_range(this->members_.m_start, iterator(*cur, cur));
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }

   template <class InpIt>
   void priv_range_initialize(InpIt first, InpIt last, std::input_iterator_tag)
   {
      this->priv_initialize_map(0);
      BOOST_TRY {
         for ( ; first != last; ++first)
            this->push_back(*first);
      }
      BOOST_CATCH(...){
         this->clear();
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }

   template <class FwdIt>
   void priv_range_initialize(FwdIt first, FwdIt last, std::forward_iterator_tag)
   {
      size_type n = 0;
      n = std::distance(first, last);
      this->priv_initialize_map(n);

      index_pointer cur_node;
      BOOST_TRY {
         for (cur_node = this->members_.m_start.m_node; 
               cur_node < this->members_.m_finish.m_node; 
               ++cur_node) {
            FwdIt mid = first;
            std::advance(mid, this->s_buffer_size());
            std::uninitialized_copy(first, mid, *cur_node);
            first = mid;
         }
         std::uninitialized_copy(first, last, this->members_.m_finish.m_first);
      }
      BOOST_CATCH(...){
         this->priv_destroy_range(this->members_.m_start, iterator(*cur_node, cur_node));
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }

   // Called only if this->members_.m_finish.m_cur == this->members_.m_finish.m_last - 1.
   void priv_push_back_aux(const value_type& t = value_type())
   {
      this->priv_reserve_map_at_back();
      *(this->members_.m_finish.m_node + 1) = this->priv_allocate_node();
      BOOST_TRY {
         new((void*)detail::get_pointer(this->members_.m_finish.m_cur))value_type(t);
         this->members_.m_finish.priv_set_node(this->members_.m_finish.m_node + 1);
         this->members_.m_finish.m_cur = this->members_.m_finish.m_first;
      }
      BOOST_CATCH(...){
         this->priv_deallocate_node(*(this->members_.m_finish.m_node + 1));
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }

   // Called only if this->members_.m_finish.m_cur == this->members_.m_finish.m_last - 1.
   #ifndef BOOST_INTERPROCESS_RVALUE_REFERENCE
   void priv_push_back_aux(const detail::moved_object<value_type> &mt)
   {
      this->priv_reserve_map_at_back();
      *(this->members_.m_finish.m_node + 1) = this->priv_allocate_node();
      BOOST_TRY {
         new((void*)detail::get_pointer(this->members_.m_finish.m_cur))value_type(mt);
         this->members_.m_finish.priv_set_node(this->members_.m_finish.m_node + 1);
         this->members_.m_finish.m_cur = this->members_.m_finish.m_first;
      }
      BOOST_CATCH(...){
         this->priv_deallocate_node(*(this->members_.m_finish.m_node + 1));
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }
   #else
   void priv_push_back_aux(value_type &&mt)
   {
      this->priv_reserve_map_at_back();
      *(this->members_.m_finish.m_node + 1) = this->priv_allocate_node();
      BOOST_TRY {
         new((void*)detail::get_pointer(this->members_.m_finish.m_cur))value_type(detail::move_impl(mt));
         this->members_.m_finish.priv_set_node(this->members_.m_finish.m_node + 1);
         this->members_.m_finish.m_cur = this->members_.m_finish.m_first;
      }
      BOOST_CATCH(...){
         this->priv_deallocate_node(*(this->members_.m_finish.m_node + 1));
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }
   #endif

   // Called only if this->members_.m_start.m_cur == this->members_.m_start.m_first.
   void priv_push_front_aux(const value_type& t)
   {
      this->priv_reserve_map_at_front();
      *(this->members_.m_start.m_node - 1) = this->priv_allocate_node();
      BOOST_TRY {
         this->members_.m_start.priv_set_node(this->members_.m_start.m_node - 1);
         this->members_.m_start.m_cur = this->members_.m_start.m_last - 1;
         new((void*)detail::get_pointer(this->members_.m_start.m_cur))value_type(t);
      }
      BOOST_CATCH(...){
         ++this->members_.m_start;
         this->priv_deallocate_node(*(this->members_.m_start.m_node - 1));
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   } 

   #ifndef BOOST_INTERPROCESS_RVALUE_REFERENCE
   void priv_push_front_aux(const detail::moved_object<value_type> &mt)
   {
      this->priv_reserve_map_at_front();
      *(this->members_.m_start.m_node - 1) = this->priv_allocate_node();
      BOOST_TRY {
         this->members_.m_start.priv_set_node(this->members_.m_start.m_node - 1);
         this->members_.m_start.m_cur = this->members_.m_start.m_last - 1;
         new((void*)detail::get_pointer(this->members_.m_start.m_cur))value_type(mt);
      }
      BOOST_CATCH(...){
         ++this->members_.m_start;
         this->priv_deallocate_node(*(this->members_.m_start.m_node - 1));
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }
   #else
   void priv_push_front_aux(value_type &&mt)
   {
      this->priv_reserve_map_at_front();
      *(this->members_.m_start.m_node - 1) = this->priv_allocate_node();
      BOOST_TRY {
         this->members_.m_start.priv_set_node(this->members_.m_start.m_node - 1);
         this->members_.m_start.m_cur = this->members_.m_start.m_last - 1;
         new((void*)detail::get_pointer(this->members_.m_start.m_cur))value_type(detail::move_impl(mt));
      }
      BOOST_CATCH(...){
         ++this->members_.m_start;
         this->priv_deallocate_node(*(this->members_.m_start.m_node - 1));
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }
   #endif

   // Called only if this->members_.m_finish.m_cur == this->members_.m_finish.m_first.
   void priv_pop_back_aux()
   {
      this->priv_deallocate_node(this->members_.m_finish.m_first);
      this->members_.m_finish.priv_set_node(this->members_.m_finish.m_node - 1);
      this->members_.m_finish.m_cur = this->members_.m_finish.m_last - 1;
      detail::get_pointer(this->members_.m_finish.m_cur)->~value_type();
   }

   // Called only if this->members_.m_start.m_cur == this->members_.m_start.m_last - 1.  Note that 
   // if the deque has at least one element (a precondition for this member 
   // function), and if this->members_.m_start.m_cur == this->members_.m_start.m_last, then the deque 
   // must have at least two nodes.
   void priv_pop_front_aux()
   {
      detail::get_pointer(this->members_.m_start.m_cur)->~value_type();
      this->priv_deallocate_node(this->members_.m_start.m_first);
      this->members_.m_start.priv_set_node(this->members_.m_start.m_node + 1);
      this->members_.m_start.m_cur = this->members_.m_start.m_first;
   }      

   iterator priv_reserve_elements_at_front(size_type n) 
   {
      size_type vacancies = this->members_.m_start.m_cur - this->members_.m_start.m_first;
      if (n > vacancies) 
         this->priv_new_elements_at_front(n - vacancies);
      return this->members_.m_start - difference_type(n);
   }

   iterator priv_reserve_elements_at_back(size_type n) 
   {
      size_type vacancies = (this->members_.m_finish.m_last - this->members_.m_finish.m_cur) - 1;
      if (n > vacancies)
         this->priv_new_elements_at_back(n - vacancies);
      return this->members_.m_finish + difference_type(n);
   }

   void priv_new_elements_at_front(size_type new_elems)
   {
      size_type new_nodes = (new_elems + this->s_buffer_size() - 1) / 
                              this->s_buffer_size();
      this->priv_reserve_map_at_front(new_nodes);
      size_type i = 1;
      BOOST_TRY {
         for (; i <= new_nodes; ++i)
            *(this->members_.m_start.m_node - i) = this->priv_allocate_node();
      }
      BOOST_CATCH(...) {
         for (size_type j = 1; j < i; ++j)
            this->priv_deallocate_node(*(this->members_.m_start.m_node - j));      
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }

   void priv_new_elements_at_back(size_type new_elems)
   {
      size_type new_nodes = (new_elems + this->s_buffer_size() - 1) 
                              / this->s_buffer_size();
      this->priv_reserve_map_at_back(new_nodes);
      size_type i;
      BOOST_TRY {
         for (i = 1; i <= new_nodes; ++i)
            *(this->members_.m_finish.m_node + i) = this->priv_allocate_node();
      }
      BOOST_CATCH(...) {
         for (size_type j = 1; j < i; ++j)
            this->priv_deallocate_node(*(this->members_.m_finish.m_node + j));      
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }

   // Makes sure the this->members_.m_map has space for new nodes.  Does not actually
   //  add the nodes.  Can invalidate this->members_.m_map pointers.  (And consequently, 
   //  deque iterators.)
   void priv_reserve_map_at_back (size_type nodes_to_add = 1) 
   {
      if (nodes_to_add + 1 > this->members_.m_map_size - (this->members_.m_finish.m_node - this->members_.m_map))
         this->priv_reallocate_map(nodes_to_add, false);
   }

   void priv_reserve_map_at_front (size_type nodes_to_add = 1) 
   {
      if (nodes_to_add > size_type(this->members_.m_start.m_node - this->members_.m_map))
         this->priv_reallocate_map(nodes_to_add, true);
   }

   void priv_reallocate_map(size_type nodes_to_add, bool add_at_front)
   {
      size_type old_num_nodes = this->members_.m_finish.m_node - this->members_.m_start.m_node + 1;
      size_type new_num_nodes = old_num_nodes + nodes_to_add;

      index_pointer new_nstart;
      if (this->members_.m_map_size > 2 * new_num_nodes) {
         new_nstart = this->members_.m_map + (this->members_.m_map_size - new_num_nodes) / 2 
                           + (add_at_front ? nodes_to_add : 0);
         if (new_nstart < this->members_.m_start.m_node)
            std::copy(this->members_.m_start.m_node, this->members_.m_finish.m_node + 1, new_nstart);
         else
            std::copy_backward(this->members_.m_start.m_node, this->members_.m_finish.m_node + 1, 
                        new_nstart + old_num_nodes);
      }
      else {
         size_type new_map_size = 
            this->members_.m_map_size + max_value(this->members_.m_map_size, nodes_to_add) + 2;

         index_pointer new_map = this->priv_allocate_map(new_map_size);
         new_nstart = new_map + (new_map_size - new_num_nodes) / 2
                              + (add_at_front ? nodes_to_add : 0);
         std::copy(this->members_.m_start.m_node, this->members_.m_finish.m_node + 1, new_nstart);
         this->priv_deallocate_map(this->members_.m_map, this->members_.m_map_size);

         this->members_.m_map = new_map;
         this->members_.m_map_size = new_map_size;
      }

      this->members_.m_start.priv_set_node(new_nstart);
      this->members_.m_finish.priv_set_node(new_nstart + old_num_nodes - 1);
   }

   // this->priv_uninitialized_copy_fill
   // Copies [first1, last1) into [first2, first2 + (last1 - first1)), and
   //  fills [first2 + (last1 - first1), last2) with x.
   void priv_uninitialized_copy_fill(iterator first1, iterator last1,
                                   iterator first2, iterator last2,
                                   const T& x)
   {
      iterator mid2 = std::uninitialized_copy(first1, last1, first2);
      BOOST_TRY {
         std::uninitialized_fill(mid2, last2, x);
      }
      BOOST_CATCH(...){
         for(;first2 != mid2; ++first2){
            detail::get_pointer(&*first2)->~value_type();
         }
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }

   // this->priv_uninitialized_fill_copy
   // Fills [result, mid) with x, and copies [first, last) into
   //  [mid, mid + (last - first)).
   iterator priv_uninitialized_fill_copy(iterator result, iterator mid,
                                       const T& x,
                                       iterator first, iterator last)
   {
      std::uninitialized_fill(result, mid, x);
      BOOST_TRY {
         return std::uninitialized_copy(first, last, mid);
      }
      BOOST_CATCH(...){
         for(;result != mid; ++result){
            detail::get_pointer(&*result)->~value_type();
         }
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }

   // this->priv_uninitialized_copy_copy
   // Copies [first1, last1) into [result, result + (last1 - first1)), and
   //  copies [first2, last2) into
   //  [result, result + (last1 - first1) + (last2 - first2)).
   template <class InpIt1, class InpIt2, class FwdIt>
   FwdIt priv_uninitialized_copy_copy(InpIt1 first1, InpIt1 last1,
                                    InpIt2 first2, InpIt2 last2,
                                    FwdIt result)
   {
      FwdIt mid = std::uninitialized_copy(first1, last1, result);
      BOOST_TRY {
         return std::uninitialized_copy(first2, last2, mid);
      }
      BOOST_CATCH(...){
         for(;result != mid; ++result){
            detail::get_pointer(&*result)->~value_type();
         }
         BOOST_RETHROW
      }
      BOOST_CATCH_END
   }
   /// @endcond
};

// Nonmember functions.
template <class T, class Alloc>
inline bool operator==(const deque<T, Alloc>& x,
                       const deque<T, Alloc>& y)
{
   return x.size() == y.size() && equal(x.begin(), x.end(), y.begin());
}

template <class T, class Alloc>
inline bool operator<(const deque<T, Alloc>& x,
                      const deque<T, Alloc>& y) 
{
   return lexicographical_compare(x.begin(), x.end(), y.begin(), y.end());
}

template <class T, class Alloc>
inline bool operator!=(const deque<T, Alloc>& x,
                       const deque<T, Alloc>& y) 
   {  return !(x == y);   }

template <class T, class Alloc>
inline bool operator>(const deque<T, Alloc>& x,
                      const deque<T, Alloc>& y) 
   {  return y < x; }

template <class T, class Alloc>
inline bool operator<=(const deque<T, Alloc>& x,
                       const deque<T, Alloc>& y) 
   {  return !(y < x); }

template <class T, class Alloc>
inline bool operator>=(const deque<T, Alloc>& x,
                       const deque<T, Alloc>& y) 
   {  return !(x < y); }

template <class T, class Alloc>
inline void swap(deque<T,Alloc>& x, deque<T,Alloc>& y) 
   {  x.swap(y);  }

/// @cond

//!has_trivial_destructor_after_move<> == true_type
//!specialization for optimizations
template <class T, class A>
struct has_trivial_destructor_after_move<deque<T, A> >
{
   enum {   value = has_trivial_destructor<A>::value  };
};
/// @endcond

}  //namespace interprocess {
}  //namespace boost {

#include <boost/interprocess/detail/config_end.hpp>

#endif //   #ifndef  BOOST_INTERPROCESS_DEQUE_HPP

