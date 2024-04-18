import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--microservice-name", type=str, help="Name of microservice")
    parser.add_argument("--load-balancer", action="store_true", help="Enable load balancer")
    parser.add_argument("--load-balancer-port", type=int, default=0, help="Port of load balancer")
    parser.add_argument("--server-port", type=int, default=0, help="Port of microservice inference server")
    args = parser.parse_args()
    assert not (args.load_balancer and args.restful_gateway), "Select only load-balancer OR restful-gateway."

    if args.load_balancer:
        assert args.load_balancer_port, "--load-balancer-port must be provided."
        print(f"Starting load balancer on port: {args.load_balancer_port}")
        launch_load_balancing_service(args.model_config, args.load_balancer_port)

    else:
        assert args.server_port, "--server-port must be provided."
        port = args.server_port
        print(f"Starting server on port: {port}")
        launch_service(port)


if __name__ == "__main__":
    main()
