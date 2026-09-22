# Applications

- [`alive`](../application/alive/usermain.c): Blinks the green LED and prints a count over UART every 500 ms.
- [`mbf_test`](../application/mbf_test/usermain.c): Tests message-buffer sending, oldest-row dropping, and receive order.
- [`rule_check_from_flash`](../application/rule_check_from_flash/usermain.c): Sends Flash rows through a queue and reports reverse-gear, high-speed rule results over UART.
- [`model_check_from_flash`](../application/model_check_from_flash/README.md): Scales Flash rows, runs the fixed st-ai autoencoder, and reports score, whether it is flagged, and inference cycles.
- [`ae_reconstruction_from_flash`](../application/ae_reconstruction_from_flash/README.md): Scales Flash rows, runs the fixed st-ai autoencoder, and reports every row's reconstruction, its error and inference cycles.
- [`scoring_and_detect_from_flash`](../application/scoring_and_detect_from_flash/README.md): Sends the Flash rows above `MIN_SPEED` through a queue, scores each with the rules and the autoencoder, and reports the rows an alarm starts and ends on.
- [`ai_can_anomaly_detection`](../application/ai_can_anomaly_detection/README.md): Reads the CAN bus into the slots, takes a row every 0.1 s, and reports each alarm. The entry itself, and the only application that needs the CAN receive callback.
- [`can_path_from_flash`](../application/can_path_from_flash/README.md): Replays Flash CAN frames into the slots, reads a row every 0.1 s, and reports the rows an alarm starts and ends on.
