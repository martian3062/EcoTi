from locust import HttpUser, between, task


class EcoTiDemoUser(HttpUser):
    wait_time = between(0.2, 1.0)

    @task(4)
    def p1_core_demo(self):
        self.client.post(
            "/api/demo/p1-core",
            json={"identifier": "+919812345678", "lang": "hi"},
            name="/api/demo/p1-core",
        )

    @task(3)
    def shield_assess(self):
        self.client.post(
            "/api/shield/assess",
            json={
                "identifier": "+919812345678",
                "lang": "en",
                "edge": True,
                "message": "CBI digital arrest. Transfer to RBI account now.",
            },
            name="/api/shield/assess",
        )

    @task(2)
    def scam_call(self):
        self.client.post(
            "/api/scam-call/analyze",
            json={"identifier": "+919812345678", "audio_ref": "demo_scam_call.wav", "edge": True},
            name="/api/scam-call/analyze",
        )

    @task(1)
    def agent_status(self):
        self.client.get("/api/agents/status", name="/api/agents/status")
