#ifndef TORRENT_SOCKS5_STREAM_HPP_INCLUDED
#define TORRENT_SOCKS5_STREAM_HPP_INCLUDED
#include "libtorrent/proxy_base.hpp"

namespace libtorrent {

class socks5_stream : public proxy_base
{
public:

	explicit socks5_stream(asio::io_service& io_service)
		: proxy_base(io_service)

	{}

	void set_username(std::string const& user
		, std::string const& password)
	{
		m_user = user;
		m_password = password;
	}


	typedef boost::function<void(asio::error_code const&)> handler_type;

	template <class Handler>
	void async_connect(endpoint_type const& endpoint, Handler const& handler)
	{
		m_remote_endpoint = endpoint;

		// the connect is split up in the following steps:
		// 1. resolve name of proxy server
		// 2. connect to proxy server
		// 3. send SOCKS5 authentication method message
		// 4. read SOCKS5 authentication response
		// 5. send username+password
		// 6. send SOCKS5 CONNECT message

		// to avoid unnecessary copying of the handler,
		// store it in a shaed_ptr
		boost::shared_ptr<handler_type> h(new handler_type(handler));

		tcp::resolver::query q(m_hostname
			, boost::lexical_cast<std::string>(m_port));
		m_resolver.async_resolve(q, boost::bind(
			&socks5_stream::name_lookup, this, _1, _2, h));
	}

private:

	void name_lookup(asio::error_code const& e, tcp::resolver::iterator i
		, boost::shared_ptr<handler_type> h);
	void connected(asio::error_code const& e, boost::shared_ptr<handler_type> h);
	void handshake1(asio::error_code const& e, boost::shared_ptr<handler_type> h);
	void handshake2(asio::error_code const& e, boost::shared_ptr<handler_type> h);
	void handshake3(asio::error_code const& e, boost::shared_ptr<handler_type> h);
	void handshake4(asio::error_code const& e, boost::shared_ptr<handler_type> h);
	void socks_connect(boost::shared_ptr<handler_type> h);
	void connect1(asio::error_code const& e, boost::shared_ptr<handler_type> h);
	void connect2(asio::error_code const& e, boost::shared_ptr<handler_type> h);
	void connect3(asio::error_code const& e, boost::shared_ptr<handler_type> h);

	// send and receive buffer
	std::vector<char> m_buffer;
	// proxy authentication
	std::string m_user;
	std::string m_password;

};

}

#endif
