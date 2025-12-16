"""
Abstract loss interface.
"""
abstract type AbstractLoss end

"Compute loss between prediction Ŷ and target Y."
function evaluate_loss end
