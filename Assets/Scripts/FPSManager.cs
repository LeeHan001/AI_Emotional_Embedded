using UnityEngine;
using TMPro;

public class FPSManager : MonoBehaviour
{
    public TextMeshProUGUI FPSText;
    private float deltaTime = 0.0f;

    void Update()
    {
        deltaTime += (Time.unscaledDeltaTime - deltaTime) * 0.1f;

        float msec = deltaTime * 1000.0f;
        float fps = 1.0f / deltaTime;

        FPSText.text = string.Format("FrameTime(ms):{0:0.0}\nFPS:({1:0.})", msec, fps);
    }
}