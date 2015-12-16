# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.provision "shell", path: "bootstrap.sh"

  config.vm.provider "virtualbox" do |v|
      v.memory = 2048
  end

  config.vm.synced_folder ".", "/vagrant"
  config.vm.synced_folder "../data/", "/vagrant/data/"  
end
