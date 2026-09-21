# Applications

- [`alive`](../application/alive/usermain.c): Blinks the green LED and prints a count over UART every 500 ms.
- [`mbf_test`](../application/mbf_test/usermain.c): Tests message-buffer sending, oldest-row dropping, and receive order.
- [`rule_check_from_flash`](../application/rule_check_from_flash/usermain.c): Sends Flash rows through a queue and reports reverse-gear, high-speed rule results over UART.
- [`model_check_from_flash`](../application/model_check_from_flash/README.md): Scales Flash rows, runs the fixed st-ai autoencoder, and reports score, decision and inference cycles.
- [`ae_reconstruction_from_flash`](../application/ae_reconstruction_from_flash/README.md): Scales Flash rows, runs the fixed st-ai autoencoder, and reports every row's reconstruction, its error and inference cycles.
