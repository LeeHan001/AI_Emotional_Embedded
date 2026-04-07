using UnityEngine;
using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

// Test Socket.py JSON sturcture definition
[Serializable]
public class PacketData
{
    public int id;
    public string command;
    public int value;
}

public class UDPJsonReceiver : MonoBehaviour
{
    Thread receiveThread;
    UdpClient client;
    public int port = 5005;

    // Keep the last received data for processing in the main thread
    public string lastJsonRaw = "";
    public bool hasNewData = false;

    void Start()
    {
        receiveThread = new Thread(new ThreadStart(ReceiveData));
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    private void ReceiveData()//Blocking [Until the data arrives] -> So use Threading
    {
        client = new UdpClient(port);
        while (true)
        {
            try
            {
                IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0); //Accept Any IP, Empty
                byte[] data = client.Receive(ref anyIP); // byte type, Reference, Want to know IP Adress

                lastJsonRaw = Encoding.UTF8.GetString(data); //Byte -> String Decoding
                hasNewData = true; 
            }
            catch (Exception e) { Debug.LogError(e.ToString()); }
        }
    }

    void Update()
    {
        if (hasNewData)
        {
            // JSON String C# Deserialize
            PacketData receivedPacket = JsonUtility.FromJson<PacketData>(lastJsonRaw);

            Debug.Log($"Data - ID: {receivedPacket.id}, Command : {receivedPacket.command}, Value : {receivedPacket.value}");

            hasNewData = false;
        }
    }

    void OnApplicationQuit()
    {
        if (receiveThread != null) receiveThread.Abort();
        if (client != null) client.Close();
    }
}