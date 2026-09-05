.class public final LX/08dR;
.super Ljava/lang/Object;


# static fields
.field public static final synthetic LIZ:I


# direct methods
.method public static constructor <clinit>()V
    .locals 1

    const v0, 0x103018

    invoke-static {v0}, Lcom/bytedance/frameworks/apm/trace/MethodCollector;->i(I)V

    invoke-static {v0}, Lcom/bytedance/frameworks/apm/trace/MethodCollector;->o(I)V

    return-void
.end method

.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()

    return-void
.end method

.method public static LIZ()Ljava/lang/String;
    .locals 1

    const-string v0, "310"

    return-object v0
.end method
