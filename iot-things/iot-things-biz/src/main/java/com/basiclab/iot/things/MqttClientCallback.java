
package com.basiclab.iot.things;

/**
 * Created by Valerii Sosliuk on 12/30/2017.
 */
public interface MqttClientCallback {

    /**
     * This method is called when the connection to the server is lost.
     *
     * @param cause the reason behind the loss of connection.
     */
    void connectionLost(Throwable cause);

    /**
     * This method is called when the connection to the server is recovered.
     *
     */
    void onSuccessfulReconnect();
}
