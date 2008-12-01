//  Copyright (c) 2001-2008 Hartmut Kaiser
// 
//  Distributed under the Boost Software License, Version 1.0. (See accompanying 
//  file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

#if !defined(BOOST_SPIRIT_KARMA_META_GRAMMAR_MARCH_26_2007_1230PM)
#define BOOST_SPIRIT_KARMA_META_GRAMMAR_MARCH_26_2007_1230PM

#include <boost/spirit/home/karma/domain.hpp>
#include <boost/spirit/home/support/placeholders.hpp>
#include <boost/spirit/home/support/meta_grammar.hpp>
#include <boost/utility/enable_if.hpp>

namespace boost { namespace spirit
{
    template <typename T, typename Functor>
    struct functor_holder;
}}

namespace boost { namespace spirit { namespace karma
{
    ///////////////////////////////////////////////////////////////////////////
    // forwards
    ///////////////////////////////////////////////////////////////////////////
    struct none;
    struct eps_generator;
    struct eol_generator;
    struct semantic_predicate;
    struct lazy_generator;
    struct functor_director;
    
    template <typename Expr, typename Enable>
    struct is_valid_expr;

    template <typename Expr, typename Enable>
    struct expr_transform;

    ///////////////////////////////////////////////////////////////////////////
    // auxiliary generators meta-grammar
    ///////////////////////////////////////////////////////////////////////////

    // none, and lazy
    struct auxiliary_meta_grammar
      : proto::or_<
            meta_grammar::empty_terminal_rule<
                karma::domain, tag::none, none>,
            meta_grammar::empty_terminal_rule<
                karma::domain, tag::eps, eps_generator>,
            meta_grammar::empty_terminal_rule<
                karma::domain, tag::eol, eol_generator>,
            meta_grammar::function1_rule<
                karma::domain, tag::eps, semantic_predicate>,
            meta_grammar::function1_rule<
                karma::domain, tag::lazy, lazy_generator>,
            meta_grammar::terminal_rule<
                karma::domain, 
                functor_holder<proto::_, proto::_>,
                functor_director
            >
        >
    {
    };

    ///////////////////////////////////////////////////////////////////////////
    //  These specializations non-intrusively hooks into the Karma meta-grammar.
    //  (see karma/meta_grammar.hpp)
    ///////////////////////////////////////////////////////////////////////////
    template <typename Expr>
    struct is_valid_expr<
            Expr,
            typename enable_if<
                proto::matches<Expr, auxiliary_meta_grammar> 
            >::type
        >
      : mpl::true_
    {
    };

    template <typename Expr>
    struct expr_transform<
            Expr,
            typename enable_if<
                proto::matches<Expr, auxiliary_meta_grammar> 
            >::type
        >
      : mpl::identity<auxiliary_meta_grammar>
    {
    };
    
}}}

#endif
