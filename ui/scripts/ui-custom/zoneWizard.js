(function($, cloudStack) {
  /**
   * Zone wizard
   */
  cloudStack.zoneWizard = function(args) {
    var renumberPhysicalNetworkForm = function($container) {
      var $items = $container.find('.select-container.multi');

      $items.each(function() {
        var $item = $(this);
        var $networkName = $item.find('.field.name input[type=text]');
        var $networkTypes = $item.find('.field.network-types input');
        var index = $item.index();

        $networkName.attr('name', 'physicalNetworks[' + index + ']' + '.name');
        $networkTypes.val(index);
      });
    };

    var addPhysicalNetwork = function($wizard) {
      var $container = $wizard.find('.setup-physical-network .content.input-area form');
      var $physicalNetworkItem = $('<div>').addClass('select-container multi');
      var $deleteButton = $('<div>').addClass('button remove physical-network')
        .attr({ title: 'Remove this physical network' })
        .append('<span>').addClass('icon').html('&nbsp;');
      var $nameField = $('<div>').addClass('field name').append(
        $('<div>').addClass('name').append(
          $('<span>').html('Network Name')
        ),
        $('<div>').addClass('value').append(
          $('<input>').attr({ type: 'text' }).addClass('required')
        )
      );
      var $dropContainer = $('<div>').addClass('drop-container').append(
        $('<span>').addClass('empty-message').html(
          'Drag and drop traffic types you would like to add here.'
        ),
        $('<ul>').hide()
      ).droppable({
        over: function(event, ui) {
          var $ul = $(this).find('ul');

          $ul.addClass('active');
          
          if (!$ul.find('li').size()) {
            $ul.fadeIn();
          }
        },

        out: function(event, ui) {
          var $ul = $(this).find('ul');

          $ul.removeClass('active');
          
          if (!$ul.find('li').size()) {
            $ul.fadeOut();
          }
        },
        
        drop: function(event, ui) {
          var $ul = $(this).find('ul');

          $ul.removeClass('active');
          ui.draggable.appendTo($ul);

          $ul.closest('.select-container.multi').siblings().each(function() {
            var $ul = $(this).find('.drop-container ul');

            if (!$ul.find('li').size()) {
              $ul.fadeOut();
            }
          });
        }
      });

      // Initialize new default network form elem
      $physicalNetworkItem.append(
        $deleteButton,
        $nameField,
        $dropContainer
      );
      $physicalNetworkItem.hide().appendTo($container).fadeIn('fast');
      renumberPhysicalNetworkForm($container);

      // Remove network action
      $physicalNetworkItem.find('.button.remove.physical-network').click(function() {
        removePhysicalNetwork($physicalNetworkItem);
      });
    };

    var removePhysicalNetwork = function($item) {
      var $container = $item.closest('.setup-physical-network .content.input-area form');

      if (!$item.siblings().size()) {
        cloudStack.dialog.notice({
          message: 'You must have at least 1 physical network'
        });
      } else if ($item.find('input[type=radio]:checked').size()) {
        cloudStack.dialog.notice({
          message: 'Please select a different public and/or management network before removing'
        });
      } else {
        // Put any traffic type symbols back in original container
        $item.find('li.traffic-type-draggable').each(function() {
          var $draggable = $(this);
          var $originalContainer = $('.traffic-types-drag-area:visible > ul > li')
            .filter(function() {
              return $(this).hasClass($draggable.attr('traffic-type-id'));
            });
          
          $draggable.appendTo($originalContainer.find('ul'));
        });

        $item.remove();
      }

      $container.validate('refresh');
    };

    return function(listViewArgs) {
      var $wizard = $('#template').find('div.zone-wizard').clone();
      var $progress = $wizard.find('div.progress ul li');
      var $steps = $wizard.find('div.steps').children().hide().filter(':not(.disabled)');
      var $diagramParts = $wizard.find('div.diagram').children().hide();

      // Close wizard
      var close = function() {
        $wizard.dialog('destroy');
        $('div.overlay').fadeOut(function() { $('div.overlay').remove(); });
      };

      // Save and close wizard
      var completeAction = function() {
        var data = cloudStack.serializeForm($wizard.find('form'));
        args.action({
          data: data,
          response: {
            success: function(args) {
              var $item = $('.list-view').listView('prependItem', {
                data: [data],
                actionFilter: function(args) { return []; }
              });

              listViewArgs.complete({
                _custom: args._custom,
                $item: $item,
                messageArgs: {
                  name: $wizard.find('div.review div.vm-instance-name input').val()
                }
              });

              close();
            },
            error: function(message) {
              $wizard.remove();
              $('div.overlay').remove();

              if (message) {
                cloudStack.dialog.notice({ message: message });
              }
            }
          }
        });
      };

      // Go to specified step in wizard,
      // updating nav items and diagram
      var showStep = function(index) {
        var targetIndex = index - 1;

        if (index <= 1) targetIndex = 0;
        if (targetIndex == $steps.size()) {
          completeAction();
        }

        var $targetStep = $($steps.hide()[targetIndex]).show();
        var formState = cloudStack.serializeForm($wizard.find('form'));

        if (!targetIndex) {
          $wizard.find('.button.previous').hide();
        } else {
          $wizard.find('.button.previous').show();
        }

        // Hide conditional fields by default
        var $conditional = $targetStep.find('.conditional');
        $conditional.hide();

        // Show conditional fields for advanced network models
        if (formState['network-model'] == 'Advanced') {
          if (formState['isolation-mode'] == 'vlan') {
            $conditional.filter('.vlan').show().find('select').trigger('change');
            if ($conditional.find('select[name=vlan-type]').val() == 'tagged') {
              $conditional.find('select.ip-scope').trigger('change');
            }
          } else if (formState['isolation-mode'] == 'security-groups') {
            $conditional.filter('.security-groups').show();
          }
        } else if (formState['network-model'] == 'Basic') {
          $conditional.filter('.basic').show();
        }

        if (!formState['public']) {
          $conditional.filter('.public').show();
        }

        // Show launch button if last step
        var $nextButton = $wizard.find('.button.next');
        $nextButton.find('span').html('Next');
        $nextButton.removeClass('final');
        if ($targetStep.index() == $steps.size() - 1) {
          $nextButton.find('span').html('Add zone');
          $nextButton.addClass('final');
        }

        // Show relevant conditional sub-step if present
        if ($targetStep.has('.wizard-step-conditional')) {
          $targetStep.find('.wizard-step-conditional').hide();
          $targetStep.find('.wizard-step-conditional.select-network').show();
        }

        // Update progress bar
        var $targetProgress = $progress.removeClass('active').filter(function() {
          return $(this).index() <= targetIndex;
        }).toggleClass('active');

        var loadData = function(options) {
          if (!options) options = {};

          args.steps[targetIndex]({
            response: {
              success: function(args) {
                $(args.domains).each(function() {
                  $('<option>').val(this.id).html(this.name)
                    .appendTo($targetStep.find('select.domain'));
                });

                $(args.networkOfferings).each(function() {
                  $('<option></option>')
                    .val(this.id)
                    .html(this.name)
                    .appendTo($targetStep.find('select.network-offering'));
                });

                $targetStep.addClass('loaded');

                // Security groups checkbox filters offering drop-down
                var $securityGroupsEnabled = $wizard.find(
                  'input[name=security-groups-enabled]'
                );
                $securityGroupsEnabled.data('target-index', targetIndex);
                $securityGroupsEnabled.change(function() {
                  var $check = $(this);
                  var $select = $targetStep.find('select.network-offering');
                  var objs = $check.is(':checked') ?
                        args.securityGroupNetworkOfferings : args.networkOfferings;

                  $select.children().remove();
                  $(objs).each(function() {
                    $('<option></option>')
                      .val(this.id)
                      .html(this.name)
                      .appendTo($select);
                  });
                });
              }
            }
          });
        };

        // Load data provider for domain dropdowns
        if (!$targetStep.hasClass('loaded') && (index == 2 || index == 4)) {
          loadData();
        }

        setTimeout(function() {
          if (!$targetStep.find('input[type=radio]:checked').size()) {
            $targetStep.find('input[type=radio]:first').click();
          }
        }, 50);

        $targetStep.find('form').validate();
      };

      // Events
      $wizard.find('select').change(function(event) {
        // Conditional selects (on step 4 mainly)
        var $target = $(this);
        var $tagged = $wizard.find('.conditional.vlan-type-tagged');
        var $untagged = $wizard.find('.conditional.vlan-type-untagged');
        var $accountSpecific = $wizard.find('.field.conditional.ip-scope-account-specific');

        // VLAN - tagged
        if ($target.is('[name=vlan-type]')) {
          $tagged.hide();
          $untagged.hide();
          $accountSpecific.hide();

          if ($target.val() == 'tagged') {
            $untagged.hide();
            $tagged.show();
          }
          else if ($target.val() == 'untagged') {
            $tagged.hide();
            $untagged.show();
          }

          $.merge($tagged, $untagged).find('select:visible').trigger('change');

          cloudStack.evenOdd($wizard, '.field:visible', {
            even: function($elem) { $elem.removeClass('odd'); $elem.addClass('even'); },
            odd: function($elem) { $elem.removeClass('even'); $elem.addClass('odd'); }
          });

          return true;
        }

        // IP Scope - acct. specific
        if ($target.is('select.ip-scope')) {
          $accountSpecific.hide();
          if ($target.val() == 'account-specific') $accountSpecific.show();

          cloudStack.evenOdd($wizard, '.field:visible', {
            even: function($elem) { $elem.removeClass('odd'); $elem.addClass('even'); },
            odd: function($elem) { $elem.removeClass('even'); $elem.addClass('odd'); }
          });
        }

        return true;
      });

      $wizard.click(function(event) {
        var $target = $(event.target);

        // Radio button
        if ($target.is('[type=radio]')) {

          if ($target.attr('name') == 'network-model') {
            var $inputs = $wizard.find('.isolation-mode').find('input[name=isolation-mode]').attr({
              disabled: 'disabled'
            });

            if ($target.val() == 'Advanced') {
              $inputs.attr('disabled', false);
            }
          }

          return true;
        }

        // Checkbox
        if ($target.is('[type=checkbox]:checked')) {
          $('div.conditional.' + $target.attr('name')).hide();

          return true;
        } else if ($target.is('[type=checkbox]:unchecked')) {
          $('div.conditional.' + $target.attr('name')).show();

          return true;
        }

        // Next button
        if ($target.closest('div.button.next').size()) {
          // Check validation first
          var $form = $steps.filter(':visible').find('form');
          if ($form.size() && !$form.valid()) {
            if ($form.find('.error:visible').size())
              return false;
          }

          showStep($steps.filter(':visible').index() + 2);

          return false;
        }

        // Previous button
        if ($target.closest('div.button.previous').size()) {
          showStep($steps.filter(':visible').index());

          return false;
        }

        // Close button
        if ($target.closest('div.button.cancel').size()) {
          close();

          return false;
        }

        // Edit link
        if ($target.closest('div.edit').size()) {
          var $edit = $target.closest('div.edit');

          showStep($edit.find('a').attr('href'));

          return false;
        }

        return true;
      });

      // Add/remove network action
      $wizard.find('.button.add.new-physical-network').click(function() {
        addPhysicalNetwork($wizard);
      });

      // Setup traffic type draggables
      $wizard.find('.traffic-type-draggable').draggable({
        appendTo: $wizard,
        helper: 'clone',

        // Events
        start: function(event, ui) {
          $(this).addClass('disabled');
        },

        stop: function(event, ui) {
          $(this).removeClass('disabled');
        }
      });

      $wizard.find('.traffic-types-drag-area').droppable({
        drop: function(event, ui) {
          var $ul = $(this).find('ul').filter(function() {
            return $(this).parent().hasClass(
              ui.draggable.attr('traffic-type-id')
            );
          });

          $ul.append(ui.draggable);
        }
      });

      // Initialize first physical network item
      addPhysicalNetwork($wizard);

      showStep(1);

      return $wizard.dialog({
        title: 'Add zone',
        width: 750,
        height: 665,
        zIndex: 5000,
        resizable: false
      }).closest('.ui-dialog').overlay();
    };
  };
})(jQuery, cloudStack);
