#ifndef __DECLSPEC_H__
#define __DECLSPEC_H__

#ifdef WIN32
	#ifdef MINIUPNP_EXPORTS
		#define LIBSPEC __declspec(dllexport)
	#else
		#define LIBSPEC __declspec(dllimport)
	#endif
#else
	#define LIBSPEC
#endif

#endif

