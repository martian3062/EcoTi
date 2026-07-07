from rest_framework import serializers


class AgentRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=False, default="+919812345678")


class ScamCallRequestSerializer(AgentRequestSerializer):
    audio_ref = serializers.CharField(required=False, default="demo_scam_call.wav")
    transcript = serializers.CharField(required=False)
    edge = serializers.BooleanField(required=False, default=False)


class ShieldRequestSerializer(AgentRequestSerializer):
    message = serializers.CharField()
    lang = serializers.ChoiceField(
        choices=["en", "hi", "ta", "kn", "te", "ml", "mr", "gu", "bn", "pa", "or", "as"],
        required=False,
        default="en",
    )
    edge = serializers.BooleanField(required=False, default=True)
    offline = serializers.BooleanField(required=False, default=True)


class P1CoreDemoRequestSerializer(AgentRequestSerializer):
    transcript = serializers.CharField(required=False)
    audio_ref = serializers.CharField(required=False, default="demo_scam_call.wav")
    lang = serializers.ChoiceField(
        choices=["en", "hi", "ta", "kn", "te", "ml", "mr", "gu", "bn", "pa", "or", "as"],
        required=False,
        default="hi",
    )


class CounterfeitRequestSerializer(serializers.Serializer):
    image_ref = serializers.CharField(required=False, default="demo_fake_500.jpg")


class GeoHotspotRequestSerializer(serializers.Serializer):
    district = serializers.CharField(required=False)


class GenericAgentResponseSerializer(serializers.Serializer):
    verdict = serializers.CharField(required=False)
    confidence = serializers.FloatField(required=False)
    route = serializers.CharField(required=False)
    event = serializers.DictField(required=False)
    fused_trust_risk = serializers.DictField(required=False)


class P1CoreDemoResponseSerializer(serializers.Serializer):
    demo = serializers.CharField()
    identifier = serializers.CharField()
    offline_proof = serializers.DictField()
    scam_call = serializers.DictField()
    citizen_shield = serializers.DictField()
    same_script_pattern = serializers.BooleanField()


class AgentStatusSerializer(serializers.Serializer):
    agent = serializers.CharField()
    status = serializers.CharField()
    detail = serializers.CharField(allow_blank=True)
    fallback_used = serializers.CharField(allow_blank=True)
    has_fallback = serializers.BooleanField()
    updated_at = serializers.DateTimeField(allow_null=True)


class EventsHistorySerializer(serializers.Serializer):
    events = serializers.ListField(child=serializers.DictField())
    fused = serializers.ListField(child=serializers.DictField())


class EvidencePacketSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    identifier = serializers.CharField()
    title = serializers.CharField()
    status = serializers.CharField()
    body = serializers.DictField()
    created_at = serializers.DateTimeField()
