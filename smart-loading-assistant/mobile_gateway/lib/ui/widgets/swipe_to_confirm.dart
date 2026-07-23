import 'package:flutter/material.dart';
import 'package:flutter/physics.dart';
import 'package:flutter/services.dart';

class SwipeToConfirmWidget extends StatefulWidget {
  final Future<void> Function() onConfirm;
  final String text;
  final double height;

  const SwipeToConfirmWidget({
    Key? key,
    required this.onConfirm,
    this.text = 'SWIPE TO CONFIRM',
    this.height = 120.0, // Oversized for thick gloves
  }) : super(key: key);

  @override
  _SwipeToConfirmWidgetState createState() => _SwipeToConfirmWidgetState();
}

class _SwipeToConfirmWidgetState extends State<SwipeToConfirmWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  bool _hasVibrated = false;
  bool _isSubmitting = false;

  final double _completionThreshold = 0.85;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController.unbounded(vsync: this);
    _controller.addListener(_onAnimationUpdate);
  }

  void _onAnimationUpdate() {
    // Lock haptics to fire exactly once per crossing
    if (_controller.value >= _completionThreshold && !_hasVibrated) {
      _hasVibrated = true;
      HapticFeedback.heavyImpact();
    } else if (_controller.value < _completionThreshold && _hasVibrated && !_isSubmitting) {
      // Reset lock if worker backs out of the swipe
      _hasVibrated = false;
    }
    setState(() {}); // Rebuild to update thumb position
  }

  void _onHorizontalDragDown(DragDownDetails details) {
    if (_isSubmitting) return; // Prevent interaction while submitting
    // Instantly kill the spring momentum to hand control back to the glove
    _controller.stop();
  }

  void _onHorizontalDragUpdate(DragUpdateDetails details) {
    if (_isSubmitting) return;

    // Use context.size to calculate drag percentage
    final RenderBox renderBox = context.findRenderObject() as RenderBox;
    final double width = renderBox.size.width;
    // The thumb width is roughly equal to widget height. We subtract it from total width.
    final double dragExtent = width - widget.height;
    
    // Increment the controller value
    double newValue = _controller.value + (details.primaryDelta! / dragExtent);
    _controller.value = newValue.clamp(0.0, 1.0);
  }

  void _onHorizontalDragEnd(DragEndDetails details) async {
    if (_isSubmitting) return;

    if (_controller.value >= _completionThreshold) {
      // Action completes
      _controller.value = 1.0;
      setState(() {
        _isSubmitting = true;
      });

      try {
        await widget.onConfirm();
      } finally {
        if (mounted) {
          setState(() {
            _isSubmitting = false;
            _hasVibrated = false;
          });
          _animateToZero();
        }
      }
    } else {
      // Finger lifted before threshold, implement forgiving spring simulation
      _animateToZero(velocity: details.primaryVelocity);
    }
  }

  void _onHorizontalDragCancel() {
    if (_isSubmitting) return;
    _animateToZero();
  }

  void _animateToZero({double? velocity}) {
    // Using a heavily damped spring so if a gloved finger drops contact,
    // the slider holds position for a fraction of a second before inertia pulls it back.
    final spring = SpringDescription(
      mass: 1.0,
      stiffness: 100.0, // Low stiffness = slow return
      damping: 15.0,    // High damping = sluggish start
    );

    // Normalize velocity for the spring (pixels/sec to percentage/sec)
    final RenderBox renderBox = context.findRenderObject() as RenderBox;
    final double dragExtent = renderBox.size.width - widget.height;
    final double normalizedVelocity = (velocity ?? 0.0) / dragExtent;

    final simulation = SpringSimulation(
      spring,
      _controller.value,
      0.0, // Target is 0
      normalizedVelocity,
    );

    _controller.animateWith(simulation);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final double width = constraints.maxWidth;
        final double thumbSize = widget.height;
        final double trackWidth = width - thumbSize;
        final double position = _controller.value * trackWidth;

        return Container(
          height: widget.height,
          decoration: BoxDecoration(
            color: Colors.grey[900],
            borderRadius: BorderRadius.circular(widget.height / 2),
            border: Border.all(color: Colors.grey[800]!, width: 2),
          ),
          child: Stack(
            children: [
              // Background Text
              Center(
                child: Opacity(
                  opacity: 1.0 - _controller.value.clamp(0.0, 1.0),
                  child: Text(
                    widget.text,
                    style: TextStyle(
                      color: Colors.white54,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2,
                    ),
                  ),
                ),
              ),
              // Track Fill (Highlights green as you drag)
              Positioned(
                left: 0,
                top: 0,
                bottom: 0,
                width: position + (thumbSize / 2),
                child: Container(
                  decoration: BoxDecoration(
                    color: _controller.value >= _completionThreshold
                        ? Colors.green[700]
                        : Colors.green[700]?.withOpacity(0.3 + (_controller.value * 0.4)),
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(widget.height / 2),
                      bottomLeft: Radius.circular(widget.height / 2),
                    ),
                  ),
                ),
              ),
              // Thumb / Dragger
              Positioned(
                left: position,
                top: 0,
                bottom: 0,
                width: thumbSize,
                child: GestureDetector(
                  onHorizontalDragDown: _onHorizontalDragDown,
                  onHorizontalDragUpdate: _onHorizontalDragUpdate,
                  onHorizontalDragEnd: _onHorizontalDragEnd,
                  onHorizontalDragCancel: _onHorizontalDragCancel,
                  child: Container(
                    decoration: BoxDecoration(
                      color: _isSubmitting ? Colors.green[600] : Colors.grey[300],
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black45,
                          blurRadius: 10,
                          offset: Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Center(
                      child: _isSubmitting
                          ? CircularProgressIndicator(color: Colors.white)
                          : Icon(
                              Icons.double_arrow,
                              color: Colors.black87,
                              size: 40,
                            ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
