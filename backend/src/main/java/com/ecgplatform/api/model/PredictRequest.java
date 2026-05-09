package com.ecgplatform.api.model;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record PredictRequest(
    @NotNull
    @Size(min = 360, max = 360, message = "signal must contain exactly 360 samples")
    List<Double> signal
) {}
